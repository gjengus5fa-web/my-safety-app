import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 구글 Gemini API 키 설정
# (주의: API 키는 외부에 유출되지 않게 조심하세요!)
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# 2. AI 모델 선택 
try:
    # 현재 API 키로 사용 가능한 전체 모델 목록을 불러옵니다.
    valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 목록 중에서 빠르고 저렴한 'flash' 모델만 찾아냅니다.
    flash_models = [name for name in valid_models if 'flash' in name]
    
    # flash 모델이 존재하면 가장 첫 번째 것을, 없으면 사용 가능한 아무 모델이나 선택합니다.
    if flash_models:
        target_model_name = flash_models[0]
    elif valid_models:
        target_model_name = valid_models[0]
    else:
        target_model_name = 'gemini-pro' # 최후의 기본값
        
    model = genai.GenerativeModel(target_model_name)
    
    # 화면에 현재 연결된 모델이 무엇인지 표시해 줍니다.
    st.info(f"💡 현재 연결된 AI 모델: {target_model_name}")

except Exception as e:
    st.error(f"모델 목록을 불러오는 중 오류가 발생했습니다: {e}")

# 3. 앱 화면 구성 시작
st.title("👷‍♂️ 찰칵! AI 안전 지킴이 (무료 버전)")
st.write("현장 사진을 올리거나 직접 촬영하면 구글 AI가 위험한 곳을 찾고 쉽게 설명해 드립니다.")

# 앱 화면에 선택 박스 만들기
check_type = st.radio(
    "어떤 위험 요소를 중점적으로 분석할까요?",
    ("전체 보기", "작업자(사람) 중심", "시설물/환경 중심", "장비/기계 중심")
)

# 4. 사진 업로드 및 📷 카메라 촬영 기능
uploaded_file = st.file_uploader("갤러리에서 사진 올리기 (jpg, png)", type=["jpg", "png", "jpeg"])

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
    
    # [🔥 추가/수정됨] 분석 속도 향상을 위해 해상도를 512x512로 축소
    image.thumbnail((512, 512))

    if st.button("🚨 위험 포인트 분석하기"):
        # 로딩 중 텍스트에 사용자가 선택한 분야를 표시합니다.
        with st.spinner(f"구글 AI가 '{check_type}' 위주로 사진을 분석 중입니다... (최대 30초 소요)"):
            try:
                # 4. [🔥 추가/수정됨] 법적 오류 방지 및 Before/After 표 작성을 위한 엄격한 프롬프트
                prompt = f"""
                당신은 '고용노동부 산업안전보건감독관'입니다. 주어진 사진을 꼼꼼히 분석하여 빠르고 명확하게(개조식 중심) 보고서를 작성하세요.
                이번 분석에서는 [{check_type}]에 중점을 두고 확인해야 합니다.

                [🚨 법적 근거 작성 엄격 규칙 - 할루시네이션 방지]
                - 산업안전보건법 및 규칙 등 법적 조항을 언급할 때, 조항 번호를 100% 확실하게 아는 경우에만 숫자를 기재하세요.
                - 조금이라도 불확실하다면 절대 번호를 지어내지 말고, "(관련 법령 위반 의심 - 세부 조항 확인 필요)"라고만 적으세요.

                아래 4가지 목차와 형식에 맞추어 출력하세요.

                1. 🔍 현장 상황 요약
                - 진행 중인 작업과 현장 상황 간략 요약.

                2. ⚠️ 주요 위험 요소 및 법적 위반 사항
                - [{check_type}] 관점에서 발견된 불안전한 행동/상태 명시.
                - 괄호 안에 위 엄격 규칙을 적용하여 법적 근거 작성.

                3. 💥 예상되는 사고 유형
                - 방치 시 발생할 수 있는 주요 사고 원인과 결과 예측.

                4. 🛡️ 즉시 조치 사항 및 Before/After 개선 표
                - 지금 당장 취해야 할 행동과 예방 대책 제시.
                - 마지막에 반드시 아래 마크다운 표 형식에 맞추어 현재 상태와 개선된 상태를 비교해 주세요 (핵심만 2줄 내외).
                | 구분 | 현재 상태 (위험 - Before) | 개선된 상태 (안전 - After) | 필요한 안전 장비/조치 |
                |---|---|---|---|
                | ... | ... | ... | ... |
                """
                
                # 5. [🔥 추가/수정됨] 속도 최적화를 위한 설정(토큰 제한 600) 및 스트리밍 활성화
                response = model.generate_content(
                    [prompt, image],
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 600
                    },
                    stream=True
                )
                
                # 6. [🔥 추가/수정됨] 답변을 실시간 타자 치듯 스트리밍으로 출력
                st.success("✅ 분석이 완료되었습니다!")
                
                result_placeholder = st.empty()
                full_response = ""
                for chunk in response:
                    full_response += chunk.text
                    result_placeholder.markdown(full_response)
                
                # 7. [🔥 추가됨] 면책 조항 경고 박스 출력
                st.warning("💡 **주의 및 안내**: AI가 제시하는 법적 위반 사항은 시각적 추정에 기반한 참고용 가이드입니다. 안전을 위해 공식적인 조치 전 반드시 현장 관리자가 최신 법령을 직접 교차 검증하시기 바랍니다.")
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
