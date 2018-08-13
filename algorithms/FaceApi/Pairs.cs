using System.Collections.Generic;
using System.IO;
using System.Threading;

namespace FaceApi
{
    class Pairs
    {
        private static readonly string[] AllowedExtensions = new[] { "png", "jpg", "jpeg" };
        private string PairsTxtPath { get; }
        private string ImagesRoot { get; }

        public Pairs(string pairsTxtPath, string imagesRoot)
        {
            PairsTxtPath = pairsTxtPath;
            ImagesRoot = imagesRoot;
        }

        public IEnumerable<Pair> Parse()
        {
            using (var stream = new StreamReader(PairsTxtPath))
            {
                string pair;
                while ((pair = stream.ReadLine()) != null)
                {
                    var pairParts = pair.Split('\t');
                    if (pairParts.Length == 3)
                    {
                        var personName = pairParts[0];
                        var image1 = pairParts[1];
                        var image2 = pairParts[2];

                        if (TryFormatImagePath(personName, image1, out string imagePath1) && TryFormatImagePath(personName, image2, out string imagePath2))
                        {
                            yield return new Pair(imagePath1, imagePath2, areSame: true);
                        }
                    }
                    else if (pairParts.Length == 4)
                    {

                        var personName1 = pairParts[0];
                        var image1 = pairParts[1];
                        var personName2 = pairParts[2];
                        var image2 = pairParts[3];

                        if (TryFormatImagePath(personName1, image1, out string imagePath1) && TryFormatImagePath(personName2, image2, out string imagePath2))
                        {
                            yield return new Pair(imagePath1, imagePath2, areSame: false);
                        }
                    }
                }
            }
        }

        private bool TryFormatImagePath(string personName, string imageNum, out string imagePath)
        {
            if (!int.TryParse(imageNum, out int imageId))
            {
                imagePath = null;
                return false;
            }

            foreach (var extension in AllowedExtensions)
            {
                var image = Path.Combine(ImagesRoot, personName, $"{personName}_{imageId.ToString("D4")}.{extension}");
                if (File.Exists(image))
                {
                    imagePath = image;
                    return true;
                }
            }

            imagePath = null;
            return false;
        }
    }

    class Pair
    {
        public string ImagePath1 { get; }
        public string ImagePath2 { get; }
        public bool AreSame { get; }

        public Pair(string imagePath1, string imagePath2, bool areSame)
        {
            ImagePath1 = imagePath1;
            ImagePath2 = imagePath2;
            AreSame = areSame;
        }
    }

    class PairStats
    {
        private int truePositives = 0;
        private int trueNegatives = 0;
        private int falsePositives = 0;
        private int falseNegatives = 0;

        public void Record(bool areSamePredicted, bool areSameActual)
        {
            if (areSamePredicted && areSameActual)
            {
                Interlocked.Increment(ref truePositives);
            }
            else if (!areSamePredicted && !areSameActual)
            {
                Interlocked.Increment(ref trueNegatives);
            }
            else if (areSamePredicted && !areSameActual)
            {
                Interlocked.Increment(ref falsePositives);
            }
            else if (!areSamePredicted && areSameActual)
            {
                Interlocked.Increment(ref falseNegatives);
            }
        }

        public double Precision
        {
            get => (truePositives) / (double)(truePositives + falsePositives);
        }

        public double Recall
        {
            get => (truePositives) / (double)(truePositives + falseNegatives);
        }

        public double Accuracy
        {
            get => (truePositives + trueNegatives) / (double)(truePositives + trueNegatives + falsePositives + falseNegatives);
        }
    }
}
