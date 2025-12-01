import streamlit as st
import os
import json # ⭐ json 모듈 추가
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 (Azure 키/엔드포인트는 .env 파일에 있어야 함)
load_dotenv()

st.set_page_config(
    page_title="F1 챗봇 기획 테스트",
    page_icon="🏎️",
    layout="wide",
)
st.title("🏎️ F1 실시간 정보 큐레이터 (Tool-Use 테스트)")
st.caption("LLM이 언제 검색(Tool)을 호출하는지 확인해 봅시다.")
st.divider()

# 2. Azure OpenAI 클라이언트 설정 (환경 변수 확인 필수!)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
)

# -----------------------------------------------------
# ⭐ Tool-Use (Function Calling) 정의 영역 ⭐
# -----------------------------------------------------

# 1. Tool 역할을 할 함수 정의 (실제 웹 검색 대신 더미 데이터 사용)
def search_web(query: str) -> str:
    """
    최신 F1 정보, 레이스 결과, 드라이버 순위 등 실시간 웹 검색이 필요할 때 사용합니다.
    """
    # 더미 검색 결과 반환
    if "스페인 GP 우승" in query or "스페인 우승" in query:
        return "웹 검색 결과: 2024년 스페인 GP에서는 Red Bull의 Max Verstappen 선수가 우승했습니다."
    elif "2025년 페라리" in query or "페라리 드라이버" in query:
        return "웹 검색 결과: 2025년 페라리 드라이버 라인업은 Charles Leclerc와 Lewis Hamilton입니다. (Hamilton은 Mercedes에서 이적)"
    else:
        # LLM이 Tool을 사용했는데 데이터가 없는 경우를 위한 일반 응답
        return f"'{query}'에 대한 웹 검색 결과는 '2024년 F1 시즌이 진행 중이며, 3주 뒤 영국 GP가 예정되어 있습니다.' 와 같습니다."

# 2. LLM에게 전달할 Tool Schema 정의
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "최신 F1 정보, **특히 2024년 이후의 레이스 결과, 드라이버 이적 뉴스, 팀 순위 변동 등** 실시간 웹 검색이 필요할 때 **반드시** 사용해야 합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "웹 검색에 사용할 정확하고 구체적인 검색어 (예: '2024년 스페인 그랑프리 우승자')."
                    }
                },
                "required": ["query"],
            },
        }
    }
]

# 3. 함수 이름과 실제 함수를 연결
AVAILABLE_FUNCTIONS = {
    "search_web": search_web,
}
# -----------------------------------------------------

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    temperature = st.slider("창의성 (temperature)", 0.0, 1.0, 0.7, 0.1)
    system_prompt = st.text_area(
        "시스템 프롬프트",
        "너는 F1 전문 분석가 챗봇이야. F1 관련 질문에 친절하고 정확하게 한국어로 답변해줘. 답변 시 항상 LLM의 자체 지식과 웹 검색 결과를 통합하여 최신 정보를 제공하려고 노력해.",
        height=150,
    )
    st.markdown("---")
    st.markdown("**Made with 💙 Streamlit + Azure OpenAI**")

# 대화기록(Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 화면에 기존 대화 내용 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 받기
if prompt := st.chat_input("F1에 대해 무엇이든 물어보세요!"):
    # (1) 사용자 메시지 화면에 표시 & 저장 (기존과 동일)
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # (2) AI 응답 생성 시작
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # ⭐ 1. LLM의 판단 없이, 코드 레벨에서 무조건 검색 함수 호출
        #    사용자의 질문(prompt)을 검색 쿼리로 사용
        message_placeholder.markdown("🧐 최신 F1 정보를 검색 중... 🔍")
        function_response = search_web(query=prompt) # search_web 함수를 직접 호출
        
        # ⭐ 2. 2차 호출을 위한 메시지 구성: 시스템 프롬프트 + 대화 기록 + 검색 결과
        messages_for_api = [
            {"role": "system", "content": system_prompt},
            *st.session_state.messages, # 기존 사용자/AI 대화 기록 모두 포함
            # 검색 결과를 LLM에게 직접 전달
            {"role": "user", "content": f"검색 결과가 다음과 같습니다: '{function_response}' 이 검색 결과를 참고하여 사용자의 마지막 질문인 '{prompt}'에 답변하세요."}
        ]

        # ⭐ 3. 단 한 번만 API 호출하여 최종 답변 생성
        message_placeholder.markdown("✨ 검색 완료! 답변을 정리하고 있어요... 🤖")
        response = client.chat.completions.create(
            model="gpt-4o-mini", # <<<< ⭐ 배포명으로 수정 필수!
            messages=messages_for_api, # 검색 결과가 포함된 메시지 전달
            temperature=temperature,
        )
        assistant_reply = response.choices[0].message.content
            
        # 최종 답변 화면에 출력 & 저장 (기존과 동일)
        message_placeholder.markdown(assistant_reply)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
