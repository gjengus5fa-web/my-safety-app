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
    
    # 2. 🔄 사진 회전 기능
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

    # 3. 회전이 완료된 사진 보여주기
    st.image(image, caption="점검할 현장 사진", use_container_width=True)
    
    if st.button("🚨 법 위반 및 위험 요소 분석하기"):
        with st.spinner(f"AI 고용노동부 감독관이 '{check_type}' 위주로 점검 중입니다..."):
            try:
                # [속도 개선] 이미지 용량 줄이기
                image.thumbnail((1024, 1024))

                # 4. AI에게 내릴 '명령어(프롬프트)' 작성 (감독관 / 산업안전보건법 양식 적용)
                prompt = f"""
                당신은 베테랑 '고용노동부 산업안전보건감독관'입니다. 주어진 사진을 꼼꼼하게 점검하고, '산업안전보건법' 및 '산업안전보건기준에 관한 규칙'을 근거로 하여 반드시 아래 제공된 4가지 목차와 형식에 맞추어 아주 상세하게 감독 점검 보고서를 작성해 주세요. 
                각 항목은 최소 3문장 이상 구체적으로 설명해야 합니다.

                특히 이번 점검에서는 [{check_type}]에 중점을 두고 법 위반 사항을 꼼꼼하게 확인해야 합니다.

                1. 🔍 현장 상황 요약
                - 사진 속 건설/산업 현장은 어떤 곳이며, 현재 어떤 작업이나 상황이 진행되고 있는지 감독관의 시선으로 묘사해 주세요.

                2. ⚠️ 주요 위험 요소 및 법령 위반 의심 사항
                - 사람의 '불안전한 행동'이나 환경의 '불안전한 상태'를 명확하게 짚어주세요. 
                - 특히 [{check_type}] 관점에서 발견된 위험 요소를 설명하고, 이와 관련된 '산업안전보건법' 또는 '안전보건규칙' 위반 의심 사항(예: 추락 방지 조치 미흡, 개인보호구 미지급/미착용, 방호장치 해체 등)을 명시해 주세요.

                3. 💥 발생 가능한 산업재해 유형
                - 이 상황을 방치할 경우 어떤 종류의 중대재해나 산업재해(추락, 붕괴, 화재, 감전, 끼임 등)가 발생할 수 있는지 구체적인 원인과 함께 예상해 주세요.

                4. 🛡️ 시정 지시 및 법적 예방 대책
                - 사고를 막기 위해 사업주 및 근로자에게 현장에서 즉시 시정하도록 지시할 사항을 엄격하게 작성해 주세요.
                - 또한, 향후 재발 방지를 위해 사업주가 반드시 준수해야 할 법적 의무 및 근본적인 안전 대책을 2가지 이상 제안해 주세요.
                """
                
                # 5. AI에게 보내고 답변 받기 (속도 개선을 위한 stream=True)
                response = model.generate_content(
                    [prompt, image],
                    generation_config={"temperature": 0.2},
                    stream=True
                )
                
                # 6. 실시간 출력
                st.success("✅ 현장 점검 분석 완료! (보고서를 작성 중입니다...)")
                st.write_stream((chunk.text for chunk in response))
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}"
