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
        private TimeLimiter RateLimit { get; }
        private FaceClient Client { get; }

        public FaceIdentifier(string apiKey, string apiEndpoint)
        {
            Client = new FaceClient(new ApiKeyServiceClientCredentials(apiKey))
            {
                Endpoint = apiEndpoint
            };

            RateLimit = TimeLimiter.GetFromMaxCountByInterval(10, TimeSpan.FromSeconds(1));
        }

        public async Task<bool> Predict(string groupId, double matchThreshold, string imagePath1, string imagePath2)
        {
            var faces = await Task.WhenAll(DetectFaces(imagePath1), DetectFaces(imagePath2));
            var result = await Client.Face.VerifyFaceToFaceAsync(faces[0][0], faces[1][0]);
            return result.Confidence >= matchThreshold;
        }

        private async Task<List<Guid>> DetectFaces(string imagePath)
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

        public async Task<string> Train(string trainSetRoot)
        {
            var groupId = Guid.NewGuid().ToString();

            await CreatePersonGroup(groupId);

            var names = Directory.GetDirectories(trainSetRoot).Select(Path.GetFileName);

            var people = await CreatePeople(groupId, names);

            await AddFaces(groupId, trainSetRoot, people);

            await TrainPersonGroup(groupId);

            return groupId;
        }

        private async Task CreatePersonGroup(string groupId)
        {
            await RateLimit.Perform(async () =>
            {
                await Client.LargePersonGroup.CreateAsync(groupId, groupId);
                await Console.Error.WriteLineAsync($"Created person group {groupId}");
            });
        }

        private async Task TrainPersonGroup(string groupId)
        {
            await RateLimit.Perform(async () =>
            {
                await Client.LargePersonGroup.TrainAsync(groupId);
                await Console.Error.WriteLineAsync($"Trained person group {groupId}");
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
}
