class FaceAnalysisError(Exception):
    pass


class ImageDoesNotExist(FaceAnalysisError):
    pass


class ImageAlreadyProcessed(FaceAnalysisError):
    pass
