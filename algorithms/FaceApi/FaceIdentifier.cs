using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Azure.CognitiveServices.Vision.Face;
using Microsoft.Azure.CognitiveServices.Vision.Face.Models;
using RateLimiter;

namespace FaceApi
{
    public class FaceIdentifier
    {
        private static readonly TimeSpan TrainingPollInterval = TimeSpan.FromSeconds(10);
        private static readonly TimeSpan RateLimitInterval = TimeSpan.FromSeconds(1);
        private static readonly int RateLimitRequests = 10;

        private TimeLimiter RateLimit { get; }
        private FaceClient Client { get; }
        private PredictionMode PredictionMode { get; }

        public FaceIdentifier(string apiKey, string apiEndpoint, PredictionMode predictionMode)
        {
            Client = new FaceClient(new ApiKeyServiceClientCredentials(apiKey))
            {
                Endpoint = apiEndpoint
            };

            RateLimit = TimeLimiter.GetFromMaxCountByInterval(RateLimitRequests, RateLimitInterval);

            PredictionMode = predictionMode;
        }

        public async Task<bool> Predict(string groupId, double matchThreshold, string imagePath1, string imagePath2)
        {
            var allFaces = await Task.WhenAll(DetectFaces(imagePath1), DetectFaces(imagePath2));
            var faces1 = allFaces[0];
            var faces2 = allFaces[1];

            if (faces1.Count == 0 || faces2.Count == 0)
            {
                return false;
            }

            switch (PredictionMode)
            {
                case PredictionMode.Identify:
                    return await PredictWithIdentify(groupId, matchThreshold, faces1, faces2);

                case PredictionMode.Verify:
                    return await PredictWithVerify(matchThreshold, faces1, faces2);

                default:
                    throw new NotImplementedException($"{PredictionMode}");
            }
        }

        public async Task<string> Train(string trainSetRoot)
        {
            var groupId = Guid.NewGuid().ToString();

            await CreatePersonGroup(groupId);

            var names = Directory.GetDirectories(trainSetRoot).Select(Path.GetFileName);

            var people = await CreatePeople(groupId, names);

            await AddFaces(groupId, trainSetRoot, people);

            var success = await TrainPersonGroup(groupId);

            return success ? groupId : null;
        }

        private async Task<IList<IdentifyResult>> IdentifyPeople(IEnumerable<Guid> faceIds, string groupId, double matchThreshold)
        {
            return await RateLimit.Perform(async () =>
            {
                var results = await Client.Face.IdentifyAsync(
                    faceIds: faceIds.ToList(),
                    largePersonGroupId: groupId,
                    confidenceThreshold: matchThreshold);

                foreach (var result in results)
                {
                    await Console.Error.WriteLineAsync($"Matched {result.Candidates.Count} people for face {result.FaceId}");
                }

                return results;
            });
        }

        private async Task<IList<Guid>> DetectFaces(string imagePath)
        {
            using (var stream = File.OpenRead(imagePath))
            {
                return await RateLimit.Perform(async () =>
                {
                    var result = await Client.Face.DetectWithStreamAsync(stream, returnFaceId: true);
                    await Console.Error.WriteLineAsync($"Got {result.Count} faces for image {imagePath}");
                    return result.Select(face => face.FaceId.Value).ToList();
                });
            }
        }

        private async Task CreatePersonGroup(string groupId)
        {
            await RateLimit.Perform(async () =>
            {
                await Client.LargePersonGroup.CreateAsync(groupId, groupId);
                await Console.Error.WriteLineAsync($"Created person group {groupId}");
            });
        }

        private async Task<bool> TrainPersonGroup(string groupId)
        {
            await RateLimit.Perform(async () =>
            {
                await Client.LargePersonGroup.TrainAsync(groupId);
            });

            while (true)
            {
                var status = await Client.LargePersonGroup.GetTrainingStatusAsync(groupId);
                switch (status.Status)
                {
                    case TrainingStatusType.Nonstarted:
                    case TrainingStatusType.Running:
                        await Console.Error.WriteLineAsync($"Training of person group {groupId} is running");
                        await Task.Delay(TrainingPollInterval);
                        break;

                    case TrainingStatusType.Succeeded:
                        await Console.Error.WriteLineAsync($"Training of person group {groupId} is done");
                        return true;

                    case TrainingStatusType.Failed:
                        await Console.Error.WriteLineAsync($"Training of person group {groupId} failed");
                        return false;
                }
            }
        }

        private async Task<IEnumerable<Person>> CreatePeople(string groupId, IEnumerable<string> names)
        {
            return await Task.WhenAll(names.Select(name =>
                RateLimit.Perform(async () =>
                {
                    var result = await Client.LargePersonGroupPerson.CreateAsync(groupId, name);
                    await Console.Error.WriteLineAsync($"Created person {name}");
                    result.Name = name;
                    return result;
                })));
        }

        private async Task<IEnumerable<PersistedFace>> AddFaces(string groupId, string trainSetRoot, IEnumerable<Person> people)
        {
            return await Task.WhenAll(people.SelectMany(person =>
                Directory.GetFiles(Path.Combine(trainSetRoot, person.Name)).Select(face =>
                    AddFace(groupId, person.PersonId, face)).Where(face => face != null)));
        }

        private async Task<PersistedFace> AddFace(string groupId, Guid personId, string facePath)
        {
            using (var stream = File.OpenRead(facePath))
            {
                return await RateLimit.Perform(async () =>
                {
                    try
                    {
                        var result = await Client.LargePersonGroupPerson.AddFaceFromStreamAsync(groupId, personId, stream);
                        await Console.Error.WriteLineAsync($"Uploaded {facePath}");
                        return result;
                    }
                    catch (Exception)
                    {
                        await Console.Error.WriteLineAsync($"Unable to upload {facePath}");
                        return null;
                    }
                });
            }
        }

        private async Task<bool> PredictWithIdentify(string groupId, double matchThreshold, IList<Guid> faces1, IList<Guid> faces2)
        {
            var allPeople = await IdentifyPeople(faces1.Concat(faces2), groupId, matchThreshold);
            var people1 = allPeople.Where(candidates => faces1.Contains(candidates.FaceId)).SelectMany(candidates => candidates.Candidates).Select(person => person.PersonId).ToHashSet();
            var people2 = allPeople.Where(candidates => faces2.Contains(candidates.FaceId)).SelectMany(candidates => candidates.Candidates).Select(person => person.PersonId).ToHashSet();

            return people1.Any(person => people2.Contains(person));
        }

        private async Task<bool> PredictWithVerify(double matchThreshold, IList<Guid> faces1, IList<Guid> faces2)
        {
            var verifications = await Task.WhenAll(faces1.SelectMany(face1 => faces2.Select(face2 =>
                Client.Face.VerifyFaceToFaceAsync(face1, face2))));

            return verifications.Any(result => result.Confidence >= matchThreshold);
        }
    }

    public enum PredictionMode
    {
        Identify,
        Verify
    }
}
