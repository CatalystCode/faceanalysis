from faceanalysis.settings import FACE_VECTORIZE_ALGORITHM

if FACE_VECTORIZE_ALGORITHM == 'FaceApi':
    from faceanalysis.domain.faceapi import process_image  # noqa: F401
    from faceanalysis.domain.faceapi import get_processing_status  # noqa: F401
    from faceanalysis.domain.faceapi import upload_image  # noqa: F401
    from faceanalysis.domain.faceapi import list_images  # noqa: F401
    from faceanalysis.domain.faceapi import lookup_matching_images  # noqa: F401,E501
else:
    from faceanalysis.domain.docker import process_image  # noqa: F401
    from faceanalysis.domain.docker import get_processing_status  # noqa: F401
    from faceanalysis.domain.docker import upload_image  # noqa: F401
    from faceanalysis.domain.docker import list_images  # noqa: F401
    from faceanalysis.domain.docker import lookup_matching_images  # noqa: F401
