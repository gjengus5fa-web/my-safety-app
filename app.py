import streamlit as st
import google.generativeai as genai
from PIL import Image

# 페이지 기본 설정
st.set_page_config(page_title="AI 현장 안전 분석기", page_icon="🚧", layout="centered")

st.title("🚧 AI 현장 안전 분석기 (초고속 & 법적 근거 강화)")
st.markdown("현장 사진을 업로드하면 30초 이내에 **위험 분석 및 Before/After 개선 표**를 제공합니다. (법적 위반 의심 사항 포함)")

# API 키 입력 (실무에서는 st.secrets 등을 활용해 숨김 처리 권장)
api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
if api_key:
    genai.configure(api_key=api_key)

# 사진 업로드 및 점검 유형 선택
uploaded_file = st.file_uploader("현장 사진을 업로드하세요", type=["jpg", "jpeg", "png"])
check_type = st.selectbox("집중 점검 유형 선택", ["추락 방지", "화재 예방", "보호구 착용", "장비/기계 안전", "기타 위험 요소"])

if uploaded_file and api_key:
    # 1. 원본 이미지 불러오기
    image = Image.open(uploaded_file)
    
    # [최적화 1] 이미지 해상도 대폭 축소 (512x512) - 분석 속도 획기적 단축
    image.thumbnail((512, 512))
    
    # 화면에는 축소 최적화된 이미지를 표시
    st.image(image, caption="업로드된 현장 사진 (분석용으로 최적화됨)", use_container_width=True)

    if st.button("🚨 안전 분석 시작"):
        try:
            # [최적화 2] 가장 빠르고 가벼운 최신 비전 모델 사용 (Flash 모델)
            model = genai.GenerativeModel("gemini-1.5-flash")

            # [최적화 3] 프롬프트 간소화 + 법 조항 할루시네이션(거짓 정보) 방지 강력 통제
            prompt = f"""
            당신은 '고용노동부 산업안전보건감독관'입니다. 
            시간 단축을 위해 부연 설명 없이 핵심만 단답형/개조식으로 빠르게 작성하세요.

            점검 포인트: [{check_type}] 중심

            1. 🔍 현장 요약
            2. ⚠️ 주요 위험 및 위반 사항 
            (※ 중요 지시: 위반이 의심되는 '산업안전보건법' 또는 '산업안전보건기준에 관한 규칙'을 괄호 안에 명시할 것. 
            단, 100% 확실한 조항 번호만 기재해야 하며, 조금이라도 불확실하면 절대 임의의 숫자를 지어내지 말 것. 
            불확실한 경우 조항 번호 대신 "(예: 추락방지 조치 의무 위반 - 세부 조항 확인 필요)"와 같이 법적 의무의 '명칭'과 '확인 필요'라는 문구를 적을 것.)
            3. 💥 예상 재해
            4. 🛡️ 즉각 시정 지시

            마지막으로 작업자가 한눈에 이해할 수 있도록 현재 상태(Before)와 개선되어야 할 상태(After)를 비교하는 표(Table)를 제공해 주세요.
            표 형식:
            | 구분 | 현재 상태 (위험 - Before) | 개선된 상태 (안전 - After) | 필요한 안전 장비/조치 |
            |---|---|---|---|
            (※ 시간 단축을 위해 표의 항목은 가장 치명적인 위험 요소 최대 2~3개까지만 작성할 것)
            """

            # [최적화 4] 법 조항과 표 생성을 고려해 출력 토큰을 600으로 제한 (시간 제어)
            generation_config = genai.GenerationConfig(
                max_output_tokens=600, 
                temperature=0.2  # 사실 기반의 일관된 답변을 위해 낮게 설정하여 환각 현상 추가 억제
            )

            with st.spinner("이미지 분석 및 법적 근거 검토 중... (약 15~25초 소요)"):
                # [최적화 5] stream=True 설정으로 사용자의 체감 대기 시간 최소화
                response = model.generate_content(
                    [prompt, image],
                    generation_config=generation_config,
                    stream=True
                )
                
                # 결과를 실시간으로 찍어줄 빈 공간(placeholder) 생성
                res_box = st.empty()
                full_text = ""
                
                # 생성되는 텍스트를 실시간으로 화면에 업데이트
                for chunk in response:
                    full_text += chunk.text
                    res_box.markdown(full_text)
                    
            # 분석이 완료된 후 면책 조항 안내문 출력
            st.warning("💡 **주의 및 안내**: AI가 제시하는 법적 위반 사항은 시각적 추정에 기반한 참고용입니다. 거짓 정보 생성을 통제했으나 AI의 특성상 오류가 있을 수 있으므로, 행정 처분이나 공식적인 조치 전 반드시 안전 관리자가 최신 법령을 교차 검증하시기 바랍니다.")
                    
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
