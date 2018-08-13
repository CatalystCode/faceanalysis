using System;
using System.Linq;
using System.Threading.Tasks;

namespace FaceApi
{
    class Cli
    {
        static void Main(string[] args)
        {
            MainAsync(args).Wait();
        }

        static async Task MainAsync(string[] args)
        {
            var settings = new Settings(args);

            var faceIdentifier = new FaceIdentifier(settings.ApiKey, settings.ApiEndpoint);

            if (settings.GroupId == null)
            {
                var trainedGroupId = await faceIdentifier.Train(settings.Args[0]);
                await Console.Out.WriteLineAsync(trainedGroupId);
            }
            else if (settings.Evaluate)
            {
                var pairs = new Pairs(settings.Args[0], settings.Args[1]).Parse();
                var stats = new PairStats();
                await Task.WhenAll(pairs.Select(async pair =>
                {
                    var areSame = await faceIdentifier.Predict(settings.GroupId, settings.MatchThreshold, pair.ImagePath1, pair.ImagePath2);
                    stats.Record(areSame, pair.AreSame);
                }));

                await Console.Out.WriteLineAsync($"Accuracy: {stats.Accuracy}");
                await Console.Out.WriteLineAsync($"Precision: {stats.Precision}");
                await Console.Out.WriteLineAsync($"Recall: {stats.Recall}");
            }
            else
            {
                var areSame = await faceIdentifier.Predict(settings.GroupId, settings.MatchThreshold, settings.Args[0], settings.Args[1]);
                await Console.Out.WriteLineAsync(areSame.ToString());
            }
        }
    }

    class Settings
    {
        public string[] Args { get; }

        public Settings(string[] args)
        {
            Args = args;
        }

        public bool Evaluate
        {
            get => Environment.GetEnvironmentVariable("FACE_API_EVALUATE") == "true";
        }

        public string ApiKey
        {
            get => Environment.GetEnvironmentVariable("FACE_API_KEY");
        }

        public string ApiEndpoint
        {
            get
            {
                var endpoint = Environment.GetEnvironmentVariable("FACE_API_ENDPOINT");
                if (endpoint != null)
                {
                    return endpoint;
                }

                var region = Environment.GetEnvironmentVariable("FACE_API_REGION");
                if (region != null)
                {
                    return $"https://{region}.api.cognitive.microsoft.com";
                }

                return null;
            }
        }

        public string GroupId
        {
            get => Environment.GetEnvironmentVariable("FACE_API_GROUP_ID");
        }

        public double MatchThreshold
        {
            get
            {
                const double defaultMatchThreshold = 0.6;
                var matchThreshold = Environment.GetEnvironmentVariable("FACE_API_MATCH_THRESHOLD");
                if (matchThreshold == null)
                {
                    return defaultMatchThreshold;
                }

                if (!double.TryParse(matchThreshold, out double parsedMatchThreshold))
                {
                    return defaultMatchThreshold;
                }

                return parsedMatchThreshold;
            }
        }
    }
}
