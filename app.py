import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 구글 Gemini API 키 설정
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# 2. AI 모델 선택
model = genai.GenerativeModel('gemini-3.8-flash')

# 3. 앱 화면 구성 시작
st.title("👷‍♂️ 찰칵! AI 안전 지킴이 (고용노동부 점검 모드)")
st.write("현장 사진을 올리거나 직접 촬영하면, AI 고용노동부 감독관이 산업안전보건법에 근거하여 위험 요소를 분석해 드립니다.")

# 앱 화면에 선택 박스 만들기
check_type = st.radio(
    "어떤 위험 요소를 중점적으로 점검할까요?",
    ("전체 보기", "작업자(사람) 중심", "시설물/환경 중심", "장비/기계 중심")
)

# 4. 사진 업로드 및 📷 카메라 촬영 기능
uploaded_file = st.file_uploader(
    "갤러리에서 사진 올리기 (여러 확장자 지원)", 
    type=["jpg", "jpeg", "png", "webp", "bmp", "gif"]
)

# 카메라 켜기 체크박스
use_camera = st.checkbox("📷 카메라 켜기 (사진을 찍으려면 체크하세요)")

camera_image = None
if use_camera:
    camera_image = st.camera_input("카메라로 사진 찍기")

# 분석할 이미지 지정
image_to_analyze = None
if camera_image is not None:
    image_to_analyze = camera_image
elif uploaded_file is not None:
    image_to_analyze = uploaded_file

# 사진이 준비되었을 때만 실행
if image_to_analyze is not None:
    image = Image.open(image_to_analyze)
    
    # 5. 🔄 사진 회전 기능
    st.write("---")
    rotation = st.radio(
        "🔄 사진 방향이 누워있다면 올바르게 회전시켜 주세요:",
        ["그대로", "오른쪽으로 90도", "180도 (뒤집기)", "왼쪽으로 90도"],
        horizontal=True
    )
    
    if rotation == "오른쪽으로 90도":
        image = image.rotate(-90, expand=True)
    elif rotation == "180도 (뒤집기)":
        image = image.rotate(180, expand=True)
    elif rotation == "왼쪽으로 90도":
        image = image.rotate(90, expand=True)

    # 6. 회전이 완료된 사진 보여주기
    st.image(image, caption="점검할 현장 사진", use_container_width=True)
    
    if st.button("🚨 법 위반 및 위험 요소 분석하기"):
        with st.spinner(f"AI 고용노동부 감독관이 '{check_type}' 위주로 점검 중입니다..."):
            try:
                # [속도 개선 1] 이미지 해상도를 800으로 추가 축소하여 전송 시간 단축
                image.thumbnail((800, 800))

                # [속도 개선 2] 프롬프트 간소화: 답변을 핵심 위주의 개조식으로 제한 (생성 시간 단축)
                prompt = f"""
                당신은 '고용노동부 산업안전보건감독관'입니다. 
                '산업안전보건법'에 근거하여 아래 4가지 목차로 감독 점검 보고서를 작성해 주세요. 
                분석 속도를 위해 각 항목은 구구절절한 설명 없이 '핵심만 간결하게 개조식(글머리 기호)'으로 1~2줄 내외로 짧게 작성하세요.

                점검 포인트: [{check_type}] 중심

                1. 🔍 현장 상황 요약
                2. ⚠️ 주요 위험 요소 및 법령 위반 의심 사항
                3. 💥 발생 가능한 산업재해 유형
                4. 🛡️ 시정 지시 및 법적 예방 대책
                """
                
                # [속도 개선 3] max_output_tokens 설정으로 불필요하게 긴 답변 생성 방지
                response = model.generate_content(
                    [prompt, image],
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 800 
                    },
                    stream=True
                )
                
                # 7. 실시간 출력 (스트리밍)
                st.success("✅ 현장 점검 분석 완료! (보고서를 작성 중입니다...)")
                st.write_stream((chunk.text for chunk in response))
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
