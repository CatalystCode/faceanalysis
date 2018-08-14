using System;
using System.IO;
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
            if (!settings.TryParse(out string apiKey, out string apiEndpoint, out double matchThreshold))
            {
                await Console.Error.WriteLineAsync("Missing api-key and api-endpoint settings");
                return;
            }

            var faceIdentifier = new FaceIdentifier(apiKey, apiEndpoint);

            if (settings.TryParseForTraining(out string trainSetRoot))
            {
                var trainedGroupId = await faceIdentifier.Train(trainSetRoot);
                await Console.Out.WriteLineAsync(trainedGroupId ?? "Training failed");
            }
            else if (settings.TryParseForEvaluation(out string pairsTxtPath, out string imagesRoot))
            {
                var pairs = new Pairs(pairsTxtPath, imagesRoot).Parse();
                var stats = new PairStats();
                await Task.WhenAll(pairs.Select(async pair =>
                {
                    try
                    {
                        var areSame = await faceIdentifier.Predict(matchThreshold, pair.ImagePath1, pair.ImagePath2);
                        stats.Record(areSame, pair.AreSame);
                    }
                    catch (Exception ex)
                    {
                        await Console.Error.WriteLineAsync(ex.ToString());
                    }
                }));

                await Console.Out.WriteLineAsync($"Accuracy: {stats.Accuracy}");
                await Console.Out.WriteLineAsync($"Precision: {stats.Precision}");
                await Console.Out.WriteLineAsync($"Recall: {stats.Recall}");
            }
            else if (settings.TryParseForPrediction(out string imagePath1, out string imagePath2))
            {
                var areSame = await faceIdentifier.Predict(matchThreshold, imagePath1, imagePath2);
                await Console.Out.WriteLineAsync(areSame.ToString());
            }
            else
            {
                await Console.Error.WriteLineAsync("Missing script settings");
            }
        }
    }

    class Settings
    {
        private string[] Args { get; }

        public Settings(string[] args)
        {
            Args = args;
        }

        public bool TryParse(out string apiKey, out string apiEndpoint, out double matchThreshold)
        {
            if (ApiKey == null || ApiEndpoint == null)
            {
                apiKey = null;
                apiEndpoint = null;
                matchThreshold = -1;
                return false;
            }

            apiKey = ApiKey;
            apiEndpoint = ApiEndpoint;
            matchThreshold = MatchThreshold;
            return true;
        }

        public bool TryParseForTraining(out string trainSetRoot)
        {
            if (GroupId != null || Args.Length != 1 || !Directory.Exists(Args[0]))
            {
                trainSetRoot = null;
                return false;
            }

            trainSetRoot = Args[0];
            return true;
        }

        public bool TryParseForEvaluation(out string pairsTxtPath, out string trainSetRoot)
        {
            if (!Evaluation || Args.Length != 2 || !File.Exists(Args[0]) || !Directory.Exists(Args[1]))
            {
                pairsTxtPath = null;
                trainSetRoot = null;
                return false;
            }

            pairsTxtPath = Args[0];
            trainSetRoot = Args[1];
            return true;
        }

        public bool TryParseForPrediction(out string imagePath1, out string imagePath2)
        {
            if (Args.Length != 2 || !File.Exists(Args[0]) || !File.Exists(Args[1]))
            {
                imagePath1 = null;
                imagePath2 = null;
                return false;
            }

            imagePath1 = Args[0];
            imagePath2 = Args[1];
            return true;
        }

        private bool Evaluation
        {
            get => Environment.GetEnvironmentVariable("FACE_API_EVALUATE") == "true";
        }

        private string ApiKey
        {
            get => Environment.GetEnvironmentVariable("FACE_API_KEY");
        }

        private string ApiEndpoint
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

        private double MatchThreshold
        {
            get
            {
                const double defaultMatchThreshold = 0.6;
                var matchThreshold = Environment.GetEnvironmentVariable("FACE_API_MATCH_THRESHOLD");

                if (matchThreshold == null || !double.TryParse(matchThreshold, out double parsedMatchThreshold))
                {
                    return defaultMatchThreshold;
                }

                return parsedMatchThreshold;
            }
        }

        private string GroupId
        {
            get => Environment.GetEnvironmentVariable("FACE_API_GROUP_ID");
        }
    }
}
