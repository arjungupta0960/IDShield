from backend.face_verification import (
    load_image,
    compare_faces
)


REFERENCE_IMAGE = "data/reference_face.jpg"
PASSPORT_FACE_IMAGE = "data/different_face.jpg"


def read_image(path):
    with open(path, "rb") as file:
        return file.read()


# Load images
reference_bytes = read_image(REFERENCE_IMAGE)
passport_bytes = read_image(PASSPORT_FACE_IMAGE)

reference_image = load_image(reference_bytes)
passport_image = load_image(passport_bytes)


# Compare faces
result = compare_faces(
    reference_image,
    passport_image
)


print("\n==============================")
print("FACE VERIFICATION RESULT")
print("==============================")

print(
    f"Status: {result['status']}"
)

print(
    f"Similarity Score: {result['score']}/100"
)

if "distance" in result:

    print(
        f"Face Distance: {result['distance']}"
    )

print(
    f"Message: {result['message']}"
)

print("==============================")