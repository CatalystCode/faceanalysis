from os.path import join, exists
import sys, getopt
from processor import normalize_images

def main(argv):
    inputdirectory = ''
    outputdirectory = ''

    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('test.py -i <inputdirectory> -o <outputdirectory>')
        sys.exit(2)

    for opt, arg in opts:
      if opt == '-h':
         print('test.py -i <inputdirectory> -o <outputdirectory>')
         sys.exit()
      elif opt in ("-i", "--idirectory"):
         inputdirectory = arg
      elif opt in ("-o", "--odirectory"):
         outputdirectory = arg

    print('Input directory is {}.'.format(inputdirectory))
    print('Output directory is {}.'.format(outputdirectory))

    normalize_images(inputdirectory, outputdirectory)

if __name__== "__main__":
    main(sys.argv[1:])