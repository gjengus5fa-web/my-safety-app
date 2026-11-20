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

# 4. 사진 업로드 및 📷 카메라 촬영 기능 (확장자 추가 및 따옴표 오류 수정)
uploaded_file = st.file_uploader(
    "갤러리에서 사진 올리기 (여러 확장자 지원)", 
    type=["jpg", "jpeg", "png", "webp", "bmp", "gif"]
)

# 카메라 켜기 체크박스
use_camera = st.checkbox("📷 카메라 켜기 (사진을 찍으려면 체크하세요)")

camera_image = None
# 체크박스에 체크가 되었을 때만 카메라 활성화
if use_camera:
    camera_image = st.camera_input("카메라로 사진 찍기")

# 두 가지(업로드 또는 촬영) 중 하나라도 사진이 들어오면 분석할 이미지로 지정
image_to_analyze = None
if camera_image is not None:
    image_to_analyze = camera_image
elif uploaded_file is not None:
    image_to_analyze = uploaded_file

# 사진이 준비되었을 때만 아래 코드 실행
if image_to_analyze is not None:
    # 1. 우선 이미지를 엽니다.
    image = Image.open(image_to_analyze)
    
    # 2. 🔄 사진 회전 기능
    st.write("---")
    rotation = st.radio(
        "🔄 사진 방향이 누워있다면 올바르게 회전시켜 주세요:",
        ["그대로", "오른쪽으로 90도", "180도 (뒤집기)", "왼쪽으로 90도"],
        horizontal=True
    )
    
    # 사용자가 선택한 값에 따라 이미지 회전 처리
    if rotation == "오른쪽으로 90도":
        image = image.rotate(-90, expand=True)
    elif rotation == "180도 (뒤집기)":
        image = image.rotate(180, expand=True)
    elif rotation == "왼쪽으로 90도":
        image = image.rotate(90, expand=True)

    # 3. 회전이 완료된 사진을 화면에 보여주기
    st.image(image, caption="분석할 사진 (이 방향으로 AI가 분석합니다)", use_container_width=True)
    
    if st.button("🚨 위험 포인트 분석하기"):
        # 로딩 중 텍스트에 사용자가 선택한 분야를 표시합니다.
        with st.spinner(f"구글 AI가 '{check_type}' 위주로 사진을 분석 중입니다..."):
            try:
                # 4. AI에게 내릴 '명령어(프롬프트)' 작성 (상세한 건설 현장 양식 적용)
                prompt = f"""
                당신은 베테랑 건설 현장 안전 관리자입니다. 주어진 사진을 꼼꼼하게 분석하고, 반드시 아래 제공된 4가지 목차와 형식에 맞추어 아주 상세하게 보고서를 작성해 주세요. 
                각 항목은 최소 3문장 이상 구체적으로 설명해야 합니다.

                특히 이번 분석에서는 [{check_type}]에 중점을 두고 꼼꼼하게 확인해야 합니다.

                1. 🔍 현장 상황 요약
                - 사진 속 건설/산업 현장은 어떤 곳이며, 현재 어떤 작업이나 상황이 진행되고 있는지 묘사해 주세요.

                2. ⚠️ 주요 위험 요소 (Unsafe Acts & Conditions)
                - 사람의 '불안전한 행동'이나 환경의 '불안전한 상태'가 있다면 명확하게 짚어주세요. 
                - 특히 [{check_type}] 관점에서 발견된 위험 요소(예: 안전모 미착용, 파손된 난간, 방호 덮개 누락 등)를 집중적으로 설명해 주세요.

                3. 💥 발생 가능한 사고 유형
                - 이 상황을 방치할 경우 어떤 종류의 사고(추락, 붕괴, 화재, 감전, 미끄러짐 등)가 발생할 수 있는지 구체적인 원인과 함께 예상해 주세요.

                4. 🛡️ 즉시 조치 사항 및 예방 대책
                - 사고를 막기 위해 지금 당장 현장에서 취해야 할 즉각적인 행동과, 앞으로 지켜야 할 근본적인 안전 수칙을 2가지 이상 제안해 주세요.
                """
                
                # 5. AI에게 명령어와 '회전이 완료된 사진'을 보내고 답변 받기
                response = model.generate_content(
                    [prompt, image],
                    generation_config={"temperature": 0.2}
                )
                
                # 6. AI가 준 답변을 화면에 예쁘게 출력하기
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.text)
                
            except Exception as e:
                # 중복되었던 에러 처리 구문을 하나로 통일했습니다.
                st.error(f"분석 중 오류가 발생했습니다: {e}")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
