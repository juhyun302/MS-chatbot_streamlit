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
st.markdown("""
<style>
/* -------------------------------------- */
/* 1. Streamlit 기본 헤더 투명화 */
.stApp header {
    background-color: transparent !important;
}

/* 2. 챗봇 답변 (Assistant) 메시지 스타일링 */
.st-emotion-cache-1jm6hrf { 
    border-left: 5px solid #FF1801; /* F1 컨셉 레드 */
    padding: 15px 15px 15px 20px; 
    border-radius: 0 8px 8px 0; 
}

/* 3. 사용자 질문 (User) 메시지 스타일링 */
.st-emotion-cache-1c9v60l {
    background-color: #f7f7f7; 
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

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
def search_dts_knowledge(query: str) -> str:
    """
    사용자의 질문과 관련된 'F1 본능의 질주'의 시즌/에피소드별 핵심 내용, 드라이버 이야기, 팀 전략 문서를 찾아 반환합니다.
    """
    if "다니엘 리카르도" in query or "르노" in query:
        return "문서 검색 결과: 다니엘 리카르도의 레드불 이적 결정과 르노에서의 새로운 시작은 '본능의 질주' S1의 주요 주제 중 하나입니다. 그의 이적 배경과 심경 변화가 잘 다뤄집니다."
    elif "하스" in query or "슈타이너" in query:
        return "문서 검색 결과: 하스 팀은 예산과 성능 문제로 어려움을 겪었으며, 팀 보스 군터 슈타이너의 거침없는 어록과 리더십이 S3와 S4에 걸쳐 집중 조명됩니다."
    elif "해밀턴" in query:
        return "문서 검색 결과: 루이스 해밀턴의 인종차별 반대 활동과 사회적 메시지 전달에 대한 내용이 S3에서 상세히 다뤄집니다. 메르세데스 팀의 압도적인 성과도 함께 나옵니다."
    else:
        return f"문서 검색 결과: '{query}'에 대한 '본능의 질주' 관련 요약 정보를 찾았습니다. 이는 F1의 복잡한 배경 지식을 쉽게 이해하는 데 도움이 될 것입니다."

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

AVAILABLE_FUNCTIONS = {
    "search_dts_knowledge": search_dts_knowledge,
}
# -----------------------------------------------------

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ F1 DTS 챗봇 설정")
    st.markdown("---")
    
    # Expander를 사용해 LLM 옵션을 접어두기 (UI 최적화)
    with st.expander("✨ LLM 개발자 옵션 변경", expanded=False): 
        temperature = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7, 0.1)
        system_prompt = st.text_area(
            "시스템 프롬프트",
            "너는 'F1 본능의 질주' 전문 큐레이터 챗봇이야. F1 입문자 민수를 돕는 것이 목표이며, 사용자의 질문이 **DTS 문서 검색이 필요한 내용(예: 배경지식, 드라이버 비화)**이라고 판단되면 **Tool을 사용하고**, 일반적인 F1 정보(예: 엔진 규정)는 자체 지식으로 답변해.",
            height=150,
        )

    # ⭐⭐ 새로운 섹션: 입문자 추천 질문 (상세 버전으로 업데이트) ⭐⭐
    st.markdown("---")
    st.subheader("❓ 입문자를 위한 추천 질문")
    st.markdown("""
        F1 입문자라면 이런 질문부터 시작해 보세요!
        
        **1. 경기/레이스 관련 질문**
        - F1 경기는 언제, 어디서 볼 수 있나요? (중계 채널, 시간대 등)
        - 그랑프리(GP)는 뭐고, 레이스 주말(Race Weekend)은 어떻게 진행돼요? (연습 주행, 예선, 본선 순서)
        - 퀄리파잉(Qualifying)은 뭐고, 왜 중요해요? (Q1, Q2, Q3 시스템)
        - 스프린트 레이스는 일반 레이스와 뭐가 다른가요? (새로운 형식에 대한 이해)
        - 세이프티 카(Safety Car)와 레드 플래그(Red Flag) 상황에서는 어떻게 돼요?

        **2. 차량/규칙 관련 질문**
        - DRS(Drag Reduction System)는 정확히 언제, 어떻게 쓸 수 있어요?
        - 하드, 미디엄, 소프트 타이어는 뭐가 다르고, 언제 써야 해요? (컴파운드 차이)
        - F1 머신은 왜 이렇게 비행기처럼 생겼어요? (에어로다이내믹스 개념)
        - 엔진은 왜 이렇게 자주 바꾸고, 바꿀 때마다 페널티를 받아요? (파워 유닛 제한 규정)
        - F1과 포뮬러 E(Formula E)는 뭐가 다른가요? (전기차와의 차이)

        **3. 팀/선수/역사 관련 질문**
        - 지금 제일 잘 나가는 팀과 선수는 누구예요? (최근 시즌 강자 파악)
        - 페라리, 메르세데스, 맥라렌 같은 자동차 회사가 왜 F1에 참가하는 거예요? (기술 개발, 마케팅)
        - F1 드라이버는 왜 연봉이 그렇게 높아요? (능력, 위험성, 인기 등)
        - F1 역사상 가장 위대한 드라이버는 누구예요? (슈마허, 세나 등 레전드 질문)
    """)
    # ⭐⭐ 섹션 종료 ⭐⭐
    
    # 챗봇 정보
    st.markdown("---")
    st.subheader("💡 프로젝트 정보")
    st.markdown("""
        **콘셉트:** F1 DTS (본능의 질주) 입문자 가이드
        
        **활용 기술:** Function Calling (Tool-Use) 기반 RAG
    """)

    st.markdown("---")
    st.markdown("Made with 💙 Streamlit + Azure OpenAI")

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
        assistant_reply = "" # assistant_reply 변수 초기화
        
        # 1차 호출을 위한 메시지 구성
        messages_for_api = [
            {"role": "system", "content": system_prompt}
        ] + st.session_state.messages
        
        # ⭐ 1차 호출: LLM이 Tool 호출을 할지 스스로 판단하게 함 (최적화)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # <<<< ⭐ 배포명으로 수정 필수!
            messages=messages_for_api,
            tools=TOOLS,             
            tool_choice="auto", # ⭐ auto로 변경!
            temperature=temperature,
        )

        assistant_message = response.choices[0].message
        
        # ⭐ Tool 호출이 필요한 경우
        if assistant_message.tool_calls and len(assistant_message.tool_calls) > 0:
            # 챗봇이 생각하는 과정 보여주기
            message_placeholder.markdown("🧐 **DTS 문서**를 검색하고 있습니다... 🔍")
            
            # Tool 호출 요청 처리 루프
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                if function_name in AVAILABLE_FUNCTIONS:
                    function_to_call = AVAILABLE_FUNCTIONS[function_name]
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        st.error("오류: LLM이 반환한 함수 인수가 유효한 JSON이 아닙니다.")
                        continue
                        
                    function_response = function_to_call(
                        query=function_args.get("query", "")
                    )

                    messages_for_api.append(assistant_message)
                    messages_for_api.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                else:
                    st.error(f"오류: 알 수 없는 함수 호출 {function_name}")
            
            # ⭐ 2차 호출: Tool 실행 결과를 LLM에게 전달하여 최종 답변 생성
            message_placeholder.markdown("✨ **DTS 문서 검색 완료!** 민수가 쉽게 이해할 수 있도록 답변을 정리하고 있어요... 🤖")
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=messages_for_api, 
                    temperature=temperature,
                )
                assistant_reply = response.choices[0].message.content
            except Exception as e:
                st.error(f"🚨 2차 API 호출 중 치명적인 오류 발생: {e}")
                assistant_reply = f"죄송합니다. 서버 문제로 답변을 생성하지 못했습니다. (오류 코드: {str(e)[:50]}...)"
            
            # 최종 답변을 Placeholder에 출력
            message_placeholder.markdown(assistant_reply)

        else:
            # ⭐ Tool 호출이 필요 없는 일반 답변 (LLM 자체 지식 사용)
            assistant_reply = assistant_message.content
            
            # UX 개선: 상태 메시지와 최종 답변을 합쳐서 Placeholder에 출력
            final_output = (
                "✅ **일반 정보:** DTS 문서 검색 없이 LLM의 자체 지식으로 답변합니다."
                "\n\n" + assistant_reply
            )
            message_placeholder.markdown(final_output)
            
        # ⭐⭐⭐ 버그 수정: 최종 답변 저장 코드를 if/else 바깥에서 단 한 번 실행
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
