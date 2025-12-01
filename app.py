import streamlit as st
import os
import json 
from openai import AzureOpenAI
from dotenv import load_dotenv

# 환경 변수 로드 (Azure 키/엔드포인트는 .env 파일에 있어야 함)
load_dotenv()

st.set_page_config(
    page_title="F1 DTS 큐레이터 챗봇",
    page_icon="🏎️",
    layout="wide",
)
st.title("🏎️ F1 본능의 질주 입문 가이드")
st.caption("수업에서 배운 Function Calling 기술을 활용합니다. (검색 대상: DTS 문서)")
st.divider()

# 2. Azure OpenAI 클라이언트 설정 
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
)

# -----------------------------------------------------
# ⭐ Tool-Use (Function Calling) 정의 영역 ⭐
# -----------------------------------------------------

# 1. Tool 역할을 할 함수 정의 (DTS 문서 검색 더미 데이터 사용)
def search_dts_knowledge(query: str) -> str:
    """
    사용자의 질문과 관련된 'F1 본능의 질주'의 시즌/에피소드별 핵심 내용, 드라이버 이야기, 팀 전략 문서를 찾아 반환합니다.
    """
    # 실제 RAG 시스템이 문서에서 찾은 내용을 반환한다고 가정
    if "다니엘 리카르도" in query or "르노" in query:
        return "문서 검색 결과: 다니엘 리카르도의 레드불 이적 결정과 르노에서의 새로운 시작은 '본능의 질주' S1의 주요 주제 중 하나입니다. 그의 이적 배경과 심경 변화가 잘 다뤄집니다."
    elif "하스" in query or "슈타이너" in query:
        return "문서 검색 결과: 하스 팀은 예산과 성능 문제로 어려움을 겪었으며, 팀 보스 군터 슈타이너의 거침없는 어록과 리더십이 S3와 S4에 걸쳐 집중 조명됩니다."
    elif "해밀턴" in query:
        return "문서 검색 결과: 루이스 해밀턴의 인종차별 반대 활동과 사회적 메시지 전달에 대한 내용이 S3에서 상세히 다뤄집니다. 메르세데스 팀의 압도적인 성과도 함께 나옵니다."
    else:
        return f"문서 검색 결과: '{query}'에 대한 '본능의 질주' 관련 요약 정보를 찾았습니다. 이는 F1의 복잡한 배경 지식을 쉽게 이해하는 데 도움이 될 것입니다."

# 2. LLM에게 전달할 Tool Schema 정의
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_dts_knowledge",
            "description": "F1 본능의 질주(DTS) 다큐멘터리 내용, 드라이버 비하인드, 팀 전략 등 배경 지식 검색이 필요할 때 반드시 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "DTS 문서에서 찾을 핵심 키워드나 질문 (예: '군터 슈타이너의 유명한 대사', '리카르도의 이적 이유')."
                    }
                },
                "required": ["query"],
            },
        }
    }
]

# 3. 함수 이름과 실제 함수를 연결
AVAILABLE_FUNCTIONS = {
    "search_dts_knowledge": search_dts_knowledge,
}
# -----------------------------------------------------

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    temperature = st.slider("창의성 (temperature)", 0.0, 1.0, 0.7, 0.1)
    system_prompt = st.text_area(
        "시스템 프롬프트",
        "너는 'F1 본능의 질주' 전문 큐레이터 챗봇이야. F1 입문자 민수를 돕는 것이 목표이며, 사용자의 질문에 대해 **반드시** Tool을 사용해서 관련 DTS 문서의 내용을 찾아온 뒤, 이를 바탕으로 **흥미롭고 쉽게** 답변해줘야 해.",
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
if prompt := st.chat_input("DTS에 대해 무엇이든 물어보세요!"):
    # (1) 사용자 메시지 화면에 표시 & 저장
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # (2) AI 응답 생성 (Function Calling 루프 시작)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1차 호출을 위한 메시지 구성
        messages_for_api = [
            {"role": "system", "content": system_prompt}
        ] + st.session_state.messages
        
        # ⭐ 1차 호출: Tool 호출을 강제 (테스트 목적)
        # 이 설정은 테스트가 성공하면 "auto"로 바꾸고 프롬프트를 강화할 수 있습니다.
        response = client.chat.completions.create(
            model="gpt-4o-mini", # <<<< ⭐ 배포명으로 수정 필수!
            messages=messages_for_api,
            tools=TOOLS,             
            tool_choice={"type": "function", "function": {"name": "search_dts_knowledge"}}, 
            temperature=temperature,
        )

        assistant_message = response.choices[0].message
        
        # ⭐ Tool 호출이 필요한 경우 (우리가 강제했으므로 이 조건문이 True여야 함)
        if assistant_message.tool_calls and len(assistant_message.tool_calls) > 0:
            # 챗봇이 생각하는 과정 보여주기
            message_placeholder.markdown("🧐 **DTS 문서**를 검색하고 있습니다... 🔍")
            
            # Tool 호출 요청 처리 루프
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                
                if function_name in AVAILABLE_FUNCTIONS:
                    function_to_call = AVAILABLE_FUNCTIONS[function_name]
                    # arguments가 JSON 문자열인지 확인 후 파싱
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        st.error("오류: LLM이 반환한 함수 인수가 유효한 JSON이 아닙니다.")
                        continue
                        
                    # 함수 실행 (DTS 문서 검색 더미 실행)
                    function_response = function_to_call(
                        query=function_args.get("query", "")
                    )

                    # Tool 실행 요청과 결과를 messages_for_api에 추가
                    messages_for_api.append(assistant_message) # 1차 응답 (Tool 요청)
                    messages_for_api.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response, # 함수 실행 결과
                        }
                    )
                else:
                    st.error(f"오류: 알 수 없는 함수 호출 {function_name}")
            
            # ⭐ 2차 호출: Tool 실행 결과를 LLM에게 전달하여 최종 답변 생성
            message_placeholder.markdown("✨ **DTS 문서 검색 완료!** 민수가 쉽게 이해할 수 있도록 답변을 정리하고 있어요... 🤖")

            try:
                # 2차 호출 시도
                response = client.chat.completions.create(
                    model="gpt-4o-mini", # <<<< ⭐ 배포명으로 수정 필수!
                    messages=messages_for_api, # Tool 실행 결과가 추가된 메시지 전달
                    temperature=temperature,
                )
    
                # 응답이 성공적으로 왔을 때
                assistant_reply = response.choices[0].message.content
    
            except Exception as e:
                # API 호출 중 오류(Error)가 발생하면 이 부분이 실행됨
                st.error(f"🚨 2차 API 호출 중 치명적인 오류 발생: {e}")
                assistant_reply = f"죄송합니다. 서버 문제로 답변을 생성하지 못했습니다. (오류 코드: {str(e)[:50]}...)"
    
            # 최종 답변 화면에 출력 & 저장
            message_placeholder.markdown(assistant_reply)
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

