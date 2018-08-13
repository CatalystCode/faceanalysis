using System;
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
                var trainedGroupId = await faceIdentifier.Train(settings.TrainSetRoot);
                await Console.Out.WriteLineAsync(trainedGroupId);
            }
            else
            {
                var areSame = await faceIdentifier.Evaluate(settings.GroupId, settings.MatchThreshold, settings.TestImage1, settings.TestImage2);
                await Console.Out.WriteLineAsync(areSame.ToString());
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

        public string TrainSetRoot
        {
            get => Args[0];
        }

        public string TestImage1
        {
            get => Args[0];
        }

        public string TestImage2
        {
            get => Args[1];
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
