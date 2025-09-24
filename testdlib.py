import cv2
import dlib

# Tải model nhận diện khuôn mặt và landmarks
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # Tải file này từ: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

def get_face_shape(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    if not faces:
        return "Không tìm thấy khuôn mặt"
    for face in faces:
        landmarks = predictor(gray, face)
        jaw = [landmarks.part(i) for i in range(0, 17)]
        # Vẽ các điểm landmarks lên ảnh
        for pt in jaw:
            cv2.circle(img, (pt.x, pt.y), 2, (0, 255, 0), -1)
        # Vẽ các đường nối các điểm cằm
        for i in range(len(jaw)-1):
            pt1 = (jaw[i].x, jaw[i].y)
            pt2 = (jaw[i+1].x, jaw[i+1].y)
            cv2.line(img, pt1, pt2, (255, 0, 0), 2)
        # Vẽ mắt trái (points 36-41)
        left_eye = [landmarks.part(i) for i in range(36, 42)]
        for i in range(len(left_eye)):
            pt1 = (left_eye[i].x, left_eye[i].y)
            pt2 = (left_eye[(i+1)%6].x, left_eye[(i+1)%6].y)
            cv2.line(img, pt1, pt2, (0, 255, 255), 2)
        # Vẽ mắt phải (points 42-47)
        right_eye = [landmarks.part(i) for i in range(42, 48)]
        for i in range(len(right_eye)):
            pt1 = (right_eye[i].x, right_eye[i].y)
            pt2 = (right_eye[(i+1)%6].x, right_eye[(i+1)%6].y)
            cv2.line(img, pt1, pt2, (0, 255, 255), 2)
        # Vẽ mũi (points 27-35)
        nose = [landmarks.part(i) for i in range(27, 36)]
        for i in range(len(nose)-1):
            pt1 = (nose[i].x, nose[i].y)
            pt2 = (nose[i+1].x, nose[i+1].y)
            cv2.line(img, pt1, pt2, (0, 0, 255), 2)
        # Vẽ miệng (points 48-59, 60-67)
        mouth_outer = [landmarks.part(i) for i in range(48, 60)]
        for i in range(len(mouth_outer)):
            pt1 = (mouth_outer[i].x, mouth_outer[i].y)
            pt2 = (mouth_outer[(i+1)%12].x, mouth_outer[(i+1)%12].y)
            cv2.line(img, pt1, pt2, (0, 128, 255), 2)
        mouth_inner = [landmarks.part(i) for i in range(60, 68)]
        for i in range(len(mouth_inner)):
            pt1 = (mouth_inner[i].x, mouth_inner[i].y)
            pt2 = (mouth_inner[(i+1)%8].x, mouth_inner[(i+1)%8].y)
            cv2.line(img, pt1, pt2, (128, 0, 255), 2)
        # Vẽ lông mày trái (points 17-21)
        left_eyebrow = [landmarks.part(i) for i in range(17, 22)]
        for i in range(len(left_eyebrow)-1):
            pt1 = (left_eyebrow[i].x, left_eyebrow[i].y)
            pt2 = (left_eyebrow[i+1].x, left_eyebrow[i+1].y)
            cv2.line(img, pt1, pt2, (0, 128, 0), 2)

        # Vẽ lông mày phải (points 22-26)
        right_eyebrow = [landmarks.part(i) for i in range(22, 27)]
        for i in range(len(right_eyebrow)-1):
            pt1 = (right_eyebrow[i].x, right_eyebrow[i].y)
            pt2 = (right_eyebrow[i+1].x, right_eyebrow[i+1].y)
            cv2.line(img, pt1, pt2, (0, 128, 0), 2)
        cv2.imshow("Landmarks & Facial Parts", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return jaw

# Ví dụ sử dụng
print(get_face_shape("/Users/nguyenvu/nhansovanmenh-backend/uploads/front_19_5092197F-11BE-4E95-B957-39CF55544CAA.jpg"))