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
    public interface IFaceIdentifier
    {
        Task<bool?> Predict(string groupId, double matchThreshold, string imagePath1, string imagePath2);
        Task<string> Train(string trainSetRoot);
    }

    abstract public class FaceIdentifierBase : IFaceIdentifier
    {
        private static readonly TimeSpan TrainingPollInterval = TimeSpan.FromSeconds(10);
        private static readonly TimeSpan RateLimitInterval = TimeSpan.FromSeconds(1);
        private static readonly int RateLimitRequests = 10;

        protected TimeLimiter RateLimit { get; }
        protected FaceClient Client { get; }

        public FaceIdentifierBase(string apiKey, string apiEndpoint)
        {
            Client = new FaceClient(new ApiKeyServiceClientCredentials(apiKey))
            {
                Endpoint = apiEndpoint
            };

            RateLimit = TimeLimiter.GetFromMaxCountByInterval(RateLimitRequests, RateLimitInterval);
        }

        abstract protected Task<TrainingStatus> GetTrainingStatus(string groupId);
        abstract protected Task<bool> Predict(string groupId, double matchThreshold, IList<Guid> faces1, IList<Guid> faces2);
        abstract protected Task Train(string trainSetRoot, string groupId);

        public async Task<bool?> Predict(string groupId, double matchThreshold, string imagePath1, string imagePath2)
        {
            var allFaces = await Task.WhenAll(DetectFaces(imagePath1), DetectFaces(imagePath2));
            var faces1 = allFaces[0];
            var faces2 = allFaces[1];

            if (faces1.Count == 0 || faces2.Count == 0)
            {
                return null;
            }

            return await Predict(groupId, matchThreshold, faces1, faces2);
        }

        public async Task<string> Train(string trainSetRoot)
        {
            var groupId = Guid.NewGuid().ToString();

            await Train(trainSetRoot, groupId);

            var success = await WaitForTrainingToFinish(groupId);
            return success ? groupId : null;
        }

        private async Task<bool> WaitForTrainingToFinish(string groupId)
        {
            while (true)
            {
                var status = await GetTrainingStatus(groupId);
                switch (status.Status)
                {
                    case TrainingStatusType.Nonstarted:
                    case TrainingStatusType.Running:
                        await Console.Error.WriteLineAsync($"Training of model {groupId} is running");
                        await Task.Delay(TrainingPollInterval);
                        break;

                    case TrainingStatusType.Succeeded:
                        await Console.Error.WriteLineAsync($"Training of model {groupId} is done");
                        return true;

                    case TrainingStatusType.Failed:
                        await Console.Error.WriteLineAsync($"Training of model {groupId} failed: ${status.Message}");
                        return false;
                }
            }
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
    }

    public class FindSimilarFaceIdentifier : FaceIdentifierBase
    {
        public FindSimilarFaceIdentifier(string apiKey, string apiEndpoint) : base(apiKey, apiEndpoint)
        {
        }

        override protected async Task<bool> Predict(string groupId, double matchThreshold, IList<Guid> faces1, IList<Guid> faces2)
        {
            var similars = await Task.WhenAll(FindSimilarFaces(faces1, groupId, matchThreshold), FindSimilarFaces(faces2, groupId, matchThreshold));
            return similars[0].Any(face => similars[1].Contains(face));
        }

        private async Task<ISet<Guid>> FindSimilarFaces(IList<Guid> faces, string groupId, double matchThreshold)
        {
            var similars = await Task.WhenAll(faces.Select(face => RateLimit.Perform(() =>
                Client.Face.FindSimilarAsync(face, largeFaceListId: groupId))));

            return similars.SelectMany(x => x)
                .Where(similar => similar.Confidence >= matchThreshold)
                .Where(similar => similar.PersistedFaceId.HasValue)
                .Select(similar => similar.PersistedFaceId.Value)
                .ToHashSet();
        }

        override protected async Task Train(string trainSetRoot, string groupId)
        {
            await RateLimit.Perform(() => Client.LargeFaceList.CreateAsync(groupId, groupId));

            await AddFaces(groupId, trainSetRoot);

            await RateLimit.Perform(() => Client.LargeFaceList.TrainAsync(groupId));
        }

        override protected async Task<TrainingStatus> GetTrainingStatus(string groupId)
        {
            return await RateLimit.Perform(() => Client.LargeFaceList.GetTrainingStatusAsync(groupId));
        }

        private async Task AddFaces(string groupId, string trainSetRoot)
        {
            var images = Directory.EnumerateDirectories(trainSetRoot).SelectMany(person => Directory.EnumerateFiles(Path.Combine(trainSetRoot, person)));

            await Task.WhenAll(images.Select(image => AddFace(groupId, image)));
        }

        private async Task<PersistedFace> AddFace(string groupId, string facePath)
        {
            using (var stream = File.OpenRead(facePath))
            {
                return await RateLimit.Perform(async () =>
                {
                    try
                    {
                        var result = await Client.LargeFaceList.AddFaceFromStreamAsync(groupId, stream, facePath);
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
    }

    abstract public class LargePersonGroupFaceIdentifier : FaceIdentifierBase
    {
        public LargePersonGroupFaceIdentifier(string apiKey, string apiEndpoint) : base(apiKey, apiEndpoint)
        {
        }

        override protected async Task Train(string trainSetRoot, string groupId)
        {
            await CreatePersonGroup(groupId);

            var names = Directory.GetDirectories(trainSetRoot).Select(Path.GetFileName);

            var people = await CreatePeople(groupId, names);

            await AddFaces(groupId, trainSetRoot, people);

            await RateLimit.Perform(() => Client.LargePersonGroup.TrainAsync(groupId));
        }

        override protected async Task<TrainingStatus> GetTrainingStatus(string groupId)
        {
            return await RateLimit.Perform(() => Client.LargePersonGroup.GetTrainingStatusAsync(groupId));
        }

        private async Task CreatePersonGroup(string groupId)
        {
            await RateLimit.Perform(async () =>
            {
                await Client.LargePersonGroup.CreateAsync(groupId, groupId);
                await Console.Error.WriteLineAsync($"Created person group {groupId}");
            });
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
    }

    public class IdentifyFaceIdentifier : LargePersonGroupFaceIdentifier
    {
        public IdentifyFaceIdentifier(string apiKey, string apiEndpoint) : base(apiKey, apiEndpoint)
        {
        }

        override protected async Task<bool> Predict(string groupId, double matchThreshold, IList<Guid> faces1, IList<Guid> faces2)
        {
            var allPeople = await IdentifyPeople(faces1.Concat(faces2), groupId, matchThreshold);
            var people1 = allPeople.Where(candidates => faces1.Contains(candidates.FaceId)).SelectMany(candidates => candidates.Candidates).Select(person => person.PersonId).ToHashSet();
            var people2 = allPeople.Where(candidates => faces2.Contains(candidates.FaceId)).SelectMany(candidates => candidates.Candidates).Select(person => person.PersonId).ToHashSet();

            return people1.Any(person => people2.Contains(person));
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
    }

    public class VerifyFaceIdentifier : LargePersonGroupFaceIdentifier
    {
        public VerifyFaceIdentifier(string apiKey, string apiEndpoint) : base(apiKey, apiEndpoint)
        {
        }

        override protected async Task<bool> Predict(string groupId, double matchThreshold, IList<Guid> faces1, IList<Guid> faces2)
        {
            var verifications = await Task.WhenAll(faces1.SelectMany(face1 => faces2.Select(face2 =>
                RateLimit.Perform(() => Client.Face.VerifyFaceToFaceAsync(face1, face2)))));

            return verifications.Any(result => result.Confidence >= matchThreshold);
        }
    }
}
