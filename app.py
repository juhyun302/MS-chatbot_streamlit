# streamlit 사용해서 배포하기
import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
 
# 1. 환경 변수 로드 (.env 파일이 같은 폴더에 있어야 함)
load_dotenv()

st.set_page_config(
    page_title="주현이의 첫 AI 챗봇",
    page_icon="🤖",
    layout="wide",  # 넓게 쓰고 싶으면 wide, 기본은 centered
)

st.title("주현이의 첫 AI 챗봇")
st.caption("Azure OpenAI + Streamlit으로 만든 간단한 챗봇입니다.")
st.divider()

# 사이드바
# 2. 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    temperature = st.slider("창의성 (temperature)", 0.0, 1.0, 0.7, 0.1)
    system_prompt = st.text_area(
        "시스템 프롬프트",
        "너는 친절한 AI 챗봇이야. 사용자의 질문에 한국어로 대답해줘.",
        height=120,
    )
    st.markdown("---")
    st.markdown("**Made with 💙 Streamlit + Azure OpenAI**")


# 2. Azure OpenAI 클라이언트 설정
# (실제 값은 .env 파일이나 여기에 직접 입력하세요)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
)
 
# 3. 대화기록(Session State) 초기화 - 이게 없으면 새로고침 때마다 대화가 날아갑니다!
if "messages" not in st.session_state:
    st.session_state.messages = []
 
# 4. 화면에 기존 대화 내용 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
 
# 5. 사용자 입력 받기
if prompt := st.chat_input("무엇을 도와드릴까요?"):
    # (1) 사용자 메시지 화면에 표시 & 저장
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 👉 시스템 프롬프트를 항상 맨 앞에 붙이기
    messages_for_api = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # (2) AI 응답 생성 (스트리밍 방식 아님, 단순 호출 예시)
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 사용하시는 배포명(Deployment Name)으로 수정 필요!
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
        )
        assistant_reply = response.choices[0].message.content
        st.markdown(assistant_reply)
 
    # (3) AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})