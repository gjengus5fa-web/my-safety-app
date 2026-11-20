import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 구글 Gemini API 키 설정
# (주의: API 키는 외부에 유출되지 않게 조심하세요!)
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# 2. AI 모델 선택
model = genai.GenerativeModel('gemini-3.8-flash')

# 3. 앱 화면 구성 시작
st.title("👷‍♂️ 찰칵! AI 안전 지킴이 (무료 버전)")
st.write("현장 사진을 올리거나 직접 촬영하면 구글 AI가 위험한 곳을 찾고 쉽게 설명해 드립니다.")

# 앱 화면에 선택 박스 만들기
check_type = st.radio(
    "어떤 위험 요소를 중점적으로 분석할까요?",
    ("전체 보기", "작업자(사람) 중심", "시설물/환경 중심", "장비/기계 중심")
)

# 4. 사진 업로드 및 📷 카메라 촬영 기능 (여기부터 수정되었습니다!)
uploaded_file = st.file_uploader("갤러리에서 사진 올리기 (jpg, png)", type=["jpg", "png", "jpeg"])
camera_photo = st.camera_input("📸 모바일에서 바로 사진 찍기")

# 두 가지(업로드 또는 촬영) 중 하나라도 사진이 들어오면 분석할 이미지로 지정
image_to_analyze = None
if camera_photo is not None:
    image_to_analyze = camera_photo
elif uploaded_file is not None:
    image_to_analyze = uploaded_file

# 사진이 준비되었을 때만 아래 코드 실행
if image_to_analyze is not None:
    # 화면에 올린/찍은 사진 보여주기
    image = Image.open(image_to_analyze)
    st.image(image, caption="분석할 사진입니다.", use_container_width=True)
    
    if st.button("🚨 위험 포인트 분석하기"):
        # 로딩 중 텍스트에 사용자가 선택한 분야를 표시합니다.
        with st.spinner(f"구글 AI가 '{check_type}' 위주로 사진을 분석 중입니다..."):
            try:
                # 5. AI에게 내릴 '명령어(프롬프트)' 작성
                # f""" """ 를 사용해 중괄호 {} 안에 사용자가 선택한 check_type이 들어가게 했습니다.
                prompt = f"""
                당신은 산업 안전 전문가입니다. 첨부된 사진을 보고 위험 요소를 분석해 주세요. 
                특히 이번 분석에서는 [{check_type}]에 중점을 두고 꼼꼼하게 확인해야 합니다.

                위험 요소를 찾을 때 다음 3가지 분야를 참고하세요:
                1. [작업자/사람]: 안전모, 안전화 등 보호구 미착용, 불안전한 작업 자세 등
                2. [시설물/환경]: 파손된 난간, 정리되지 않은 바닥, 추락/붕괴 위험물, 어두운 조명 등
                3. [장비/기계]: 방호 덮개가 없는 기계, 피복이 벗겨진 전선, 안전핀이 뽑힌 소화기 등

                위험 요소를 발견하면 다음 양식에 맞춰 답변해 주세요.
                - 카테고리: (사람 / 시설물 / 장비 중 택 1)
                - 위험 원인: (왜 위험한지 초등학생도 이해할 수 있게 쉬운 설명)
                - 관련 법규: (산업안전보건법 등 관련 규정)
                - 해결책: (즉시 취해야 할 행동)
                """
                
                # 6. AI에게 사진과 명령어를 보내고 답변 받기
                response = model.generate_content([prompt, image])
                
                # 7. AI가 준 답변을 화면에 예쁘게 출력하기
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")