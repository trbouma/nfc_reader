import face_recognition

# Load the images
image_1 = face_recognition.load_image_file("images/person1.jpg")
image_2 = face_recognition.load_image_file("imanges/person2.jpg")

# Get face encodings (returns a list of face encodings in the image)
encoding_1 = face_recognition.face_encodings(image_1)[0]
encoding_2 = face_recognition.face_encodings(image_2)[0]

# Compare the faces
results = face_recognition.compare_faces([encoding_1], encoding_2)

if results[0]:
    print("✅ It's a match!")
else:
    print("❌ Not a match.")
