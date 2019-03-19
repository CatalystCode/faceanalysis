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
            if (!settings.TryParse(out IFaceIdentifier faceIdentifier, out double matchThreshold))
            {
                await Console.Error.WriteLineAsync("Missing api-key and api-endpoint settings");
                return;
            }

            if (settings.TryParseForTraining(out string trainSetRoot, out string groupId))
            {
                groupId = await faceIdentifier.Train(trainSetRoot, groupId);
                await Console.Out.WriteLineAsync(groupId ?? "Training failed");
            }
            else if (settings.TryParseForEvaluation(out string evaluationGroupId, out string pairsTxtPath, out string imagesRoot, out bool ignoreMissingEmbeddings))
            {
                var pairs = new Pairs(pairsTxtPath, imagesRoot).Parse();
                var stats = new PairStats();
                await Task.WhenAll(pairs.Select(async pair =>
                {
                    try
                    {
                        var areSame = await faceIdentifier.Predict(evaluationGroupId, matchThreshold, pair.ImagePath1, pair.ImagePath2);
                        if (areSame.HasValue)
                        {
                            stats.Record(areSame.Value, pair.AreSame);
                        }
                        else if (!ignoreMissingEmbeddings)
                        {
                            stats.Record(!pair.AreSame, pair.AreSame);
                        }

                        if (!areSame.HasValue)
                        {
                            stats.RecordMissing();
                        }
                    }
                    catch (Exception ex)
                    {
                        await Console.Error.WriteLineAsync(ex.ToString());
                    }
                }));

                await Console.Out.WriteLineAsync($"Accuracy: {stats.Accuracy}");
                await Console.Out.WriteLineAsync($"Precision: {stats.Precision}");
                await Console.Out.WriteLineAsync($"Recall: {stats.Recall}");
                await Console.Out.WriteLineAsync($"Missing: {stats.Missing}");
            }
            else if (settings.TryParseForPrediction(out string predictionGroupId, out string imagePath1, out string imagePath2))
            {
                var areSame = await faceIdentifier.Predict(predictionGroupId, matchThreshold, imagePath1, imagePath2);
                await Console.Out.WriteLineAsync(areSame.HasValue ? areSame.ToString() : "Failed to find faces");
            }
            else
            {
                await Console.Error.WriteLineAsync("Missing script settings");
            }
        }
    }

    class Settings
    {
        private static readonly PredictionMode DefaultPredictionMode = PredictionMode.Identify;
        private static readonly double DefaultMatchThreshold = 0.6;

        private string[] Args { get; }

        public Settings(string[] args)
        {
            Args = args;
        }

        public bool TryParse(out IFaceIdentifier faceIdentifier, out double matchThreshold)
        {
            if (ApiKey == null || ApiEndpoint == null || FaceIdentifier == null)
            {
                faceIdentifier = null;
                matchThreshold = DefaultMatchThreshold;
                return false;
            }

            faceIdentifier = FaceIdentifier;
            matchThreshold = MatchThreshold;
            return true;
        }

        public bool TryParseForTraining(out string trainSetRoot, out string groupId)
        {
            if (Args.Length == 0 || !Directory.Exists(Args[0]))
            {
                trainSetRoot = null;
                groupId = GroupId;
                return false;
            }

            trainSetRoot = Args[0];
            groupId = GroupId;
            return true;
        }

        public bool TryParseForEvaluation(out string groupId, out string pairsTxtPath, out string trainSetRoot, out bool ignoreMissingEmbeddings)
        {
            if (!Evaluation || GroupId == null || Args.Length != 2 || !File.Exists(Args[0]) || !Directory.Exists(Args[1]))
            {
                groupId = null;
                pairsTxtPath = null;
                trainSetRoot = null;
                ignoreMissingEmbeddings = IgnoreMissingEmbeddings;
                return false;
            }

            groupId = GroupId;
            pairsTxtPath = Args[0];
            trainSetRoot = Args[1];
            ignoreMissingEmbeddings = IgnoreMissingEmbeddings;
            return true;
        }

        public bool TryParseForPrediction(out string groupId, out string imagePath1, out string imagePath2)
        {
            if (GroupId == null || Args.Length != 2 || !File.Exists(Args[0]) || !File.Exists(Args[1]))
            {
                groupId = null;
                imagePath1 = null;
                imagePath2 = null;
                return false;
            }

            groupId = GroupId;
            imagePath1 = Args[0];
            imagePath2 = Args[1];
            return true;
        }

        private IFaceIdentifier FaceIdentifier
        {
            get
            {
                switch (PredictionMode)
                {
                    case PredictionMode.FindSimilar:
                        return new FindSimilarFaceIdentifier(ApiKey, ApiEndpoint);
                    case PredictionMode.Identify:
                        return new IdentifyFaceIdentifier(ApiKey, ApiEndpoint);
                    case PredictionMode.Verify:
                        return new VerifyFaceIdentifier(ApiKey, ApiEndpoint);
                    default:
                        return null;
                }
            }
        }

        private bool Evaluation
        {
            get => Environment.GetEnvironmentVariable("FACE_API_EVALUATE") == "true";
        }

        private bool IgnoreMissingEmbeddings
        {
            get => Environment.GetEnvironmentVariable("FACE_API_IGNORE_MISSING_EMBEDDINGS") == "true";
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
                var matchThreshold = Environment.GetEnvironmentVariable("FACE_API_MATCH_THRESHOLD");

                if (matchThreshold == null || !double.TryParse(matchThreshold, out double parsedMatchThreshold))
                {
                    return DefaultMatchThreshold;
                }

                return parsedMatchThreshold;
            }
        }

        private PredictionMode PredictionMode
        {
            get
            {
                var predictionMode = Environment.GetEnvironmentVariable("FACE_API_PREDICTION_MODE");

                if (predictionMode == null || !Enum.TryParse(typeof(PredictionMode), predictionMode, out object parsedPredictionMode))
                {
                    return DefaultPredictionMode;
                }

                return (PredictionMode)parsedPredictionMode;
            }
        }

        private string GroupId
        {
            get => Environment.GetEnvironmentVariable("FACE_API_GROUP_ID");
        }
    }

    enum PredictionMode
    {
        FindSimilar,
        Identify,
        Verify
    }
}
