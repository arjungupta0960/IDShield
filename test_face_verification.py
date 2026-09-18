"""Run a manual face-comparison check with two supplied image files.

This is an executable example, not an automated test. Keeping all work inside
``main`` lets test discovery import this module without trying to read local
files that are deliberately excluded from the repository.
"""

import argparse
from pathlib import Path

from backend.face_verification import compare_faces, load_image


def read_image(path):
    with open(path, "rb") as file:
        return file.read()


def main():
    parser = argparse.ArgumentParser(
        description="Compare a reference face with a document-face image."
    )
    parser.add_argument("reference_image", type=Path)
    parser.add_argument("passport_face_image", type=Path)
    args = parser.parse_args()

    for image_path in (args.reference_image, args.passport_face_image):
        if not image_path.is_file():
            parser.error(f"Image file was not found: {image_path}")

    result = compare_faces(
        load_image(read_image(args.reference_image)),
        load_image(read_image(args.passport_face_image)),
    )

    print("\n==============================")
    print("FACE VERIFICATION RESULT")
    print("==============================")
    print(f"Status: {result['status']}")
    print(f"Similarity Score: {result['score']}/100")

    if "distance" in result:
        print(f"Face Distance: {result['distance']}")

    print(f"Message: {result['message']}")
    print("==============================")


if __name__ == "__main__":
    main()
