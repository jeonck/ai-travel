import streamlit as st
from openai import OpenAI
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state at the very beginning
if 'stage' not in st.session_state:
    st.session_state.stage = 1

def initialize_session_state():
    """Initialize all session state variables"""
    default_values = {
        'stage': 1,
        'user_input': "",
        'recommendations': "",
        'selected_destination': "",
        'itinerary': "",
        'chat_history': [],
        'api_key': os.getenv("OPENAI_API_KEY", "")
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def validate_api_key():
    api_key = st.session_state.get('api_key', '')
    if not api_key:
        st.sidebar.error("OpenAI API key를 입력해주세요.")
        return False
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        st.sidebar.error(f"API 키 설정 중 오류가 발생했습니다: {e}")
        return False

# 앱 시작
def main():
    # 앱 제목 설정
    st.title("AI 여행 추천 도우미")
    st.write("여행 취향을 알려주시면 맞춤형 여행지를 추천해 드립니다!")
    
    # API 키 입력 (사이드바)
    st.sidebar.title("API 설정")
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        key="api_key",
        help="OpenAI API 키를 입력하세요. 입력된 키는 세션에만 저장됩니다."
    )

    # 세션 상태 초기화
    initialize_session_state()
    
    # API 키 검증 및 클라이언트 설정
    client = validate_api_key()
    if not client:
        st.stop()

    # 단계 1: 여행지 추천 받기
    if st.session_state.stage == 1:
        st.header("1단계: 여행 취향 알려주기")
        
        # 사용자 입력 받기
        user_input = st.text_area(
            "여행 취향을 자세히 알려주세요 (예: 선호하는 날씨, 활동, 음식, 예산 등)",
            placeholder="나는 여름 휴가를 계획 중이야. 따뜻한 날씨를 좋아하고, 자연 경관과 역사적인 장소를 둘러보는 걸 좋아해. 어떤 여행지가 나에게 적합할까?"
        )
        
        if st.button("여행지 추천 받기"):
            if user_input:
                st.session_state.user_input = user_input
                
                # 프롬프트 구성
                prompt = f"""
                사용자의 여행 취향을 바탕으로 적합한 여행지 3곳을 추천하세요. 
                - 먼저 사용자가 입력한 희망사항을 요약해줘
                - 사용자가 입력한 희망사항을 반영해서 왜 적합한 여행지인지 설명해주세요
                - 각 여행지의 기후, 주요 관광지, 활동 등을 설명하세요.

                사용자 입력: {user_input}
                """
                
                with st.spinner("여행지를 추천 중입니다..."):
                    recommendations = get_openai_response(prompt)
                    st.session_state.recommendations = recommendations
                    st.session_state.stage = 2
                    st.rerun()
            else:
                st.warning("여행 취향을 입력해주세요.")

    # 단계 2: 여행지 선택하기
    elif st.session_state.stage == 2:
        st.header("2단계: 여행지 선택하기")
        
        # 이전 단계 결과 표시
        st.subheader("여행 취향")
        st.write(st.session_state.user_input)
        
        st.subheader("추천 여행지")
        st.write(st.session_state.recommendations)
        
        # 사용자 선택 받기
        user_selection = st.text_area(
            "위 추천 여행지 중 하나를 선택하고 이유를 알려주세요",
            placeholder="저는 이탈리아, 토스카나를 선택하고 싶습니다. 와인과 역사적인 장소를 좋아하기 때문입니다."
        )
        
        if st.button("선택 완료"):
            if user_selection:
                # 프롬프트 구성
                prompt = f"""
                다음 여행지 3곳 중 하나를 선택하세요. 선택한 여행지 알려주세요. 그리고 선택한 이유를 설명해주세요.
                - 해당 여행지에서 즐길 수 있는 주요 활동 5가지를 나열하세요. 
                - 활동은 자연 탐방, 역사 탐방, 음식 체험 등 다양한 범주에서 포함되도록 하세요.

                사용자 입력: {user_selection}
                """
                
                context = f"""
                ### 사용자 희망사항
                {st.session_state.user_input}
                
                ### 추천 여행지
                {st.session_state.recommendations}
                """
                
                with st.spinner("선택한 여행지에 대한 정보를 가져오는 중..."):
                    selected_destination = get_openai_response(prompt, context)
                    st.session_state.selected_destination = selected_destination
                    st.session_state.stage = 3
                    st.rerun()
            else:
                st.warning("여행지를 선택해주세요.")
        
        if st.button("이전 단계로"):
            st.session_state.stage = 1
            st.rerun()

    # 단계 3: 일정 계획 받기
    elif st.session_state.stage == 3:
        st.header("3단계: 일정 계획 받기")
        
        # 이전 단계 결과 표시
        st.subheader("선택한 여행지")
        st.write(st.session_state.selected_destination)
        
        if st.button("하루 일정 계획 받기"):
            # 프롬프트 구성
            prompt = """
            사용자가 하루 동안 이 여행지에서 시간을 보낼 계획입니다. 
            - 오전, 오후, 저녁으로 나누어 일정을 짜고, 각 시간대에 어떤 활동을 하면 좋을지 설명하세요.
            """
            
            context = f"""
            ### 사용자 희망사항
            {st.session_state.user_input}
            
            ### 선택한 여행지 정보
            {st.session_state.selected_destination}
            """
            
            with st.spinner("하루 일정을 계획 중입니다..."):
                itinerary = get_openai_response(prompt, context)
                st.session_state.itinerary = itinerary
                st.subheader("하루 일정 계획")
                st.write(itinerary)
        
        # 이미 일정이 있으면 표시
        if st.session_state.itinerary:
            st.subheader("하루 일정 계획")
            st.write(st.session_state.itinerary)
        
        # 추가 질문 받기
        additional_question = st.text_area(
            "추가 질문이 있으시면 입력해주세요",
            placeholder="이 여행지에서 꼭 먹어봐야 할 음식은 무엇인가요?"
        )
        
        if st.button("질문하기") and additional_question:
            context = f"""
            ### 사용자 희망사항
            {st.session_state.user_input}
            
            ### 선택한 여행지 정보
            {st.session_state.selected_destination}
            
            ### 하루 일정 계획
            {st.session_state.itinerary}
            """
            
            with st.spinner("답변을 생성 중입니다..."):
                answer = get_openai_response(additional_question, context)
                st.subheader("답변")
                st.write(answer)
        
        if st.button("새로운 여행 계획하기"):
            # 세션 상태 초기화
            st.session_state.stage = 1
            st.session_state.user_input = ""
            st.session_state.recommendations = ""
            st.session_state.selected_destination = ""
            st.session_state.itinerary = ""
            st.session_state.chat_history = []
            st.rerun()
        
        if st.button("이전 단계로"):
            st.session_state.stage = 2
            st.rerun()

# OpenAI API 호출 함수 업데이트
def get_openai_response(prompt, context="", model="gpt-4"):
    try:
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        
        # 이전 대화 기록 추가
        for message in st.session_state.chat_history:
            messages.append(message)
            
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        # 응답 저장
        response_content = response.choices[0].message.content
        assistant_message = {"role": "assistant", "content": response_content}
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append(assistant_message)
        
        return response_content
    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요."

# 앱 정보 표시
st.sidebar.title("AI 여행 추천 도우미")
st.sidebar.write("OpenAI API를 활용한 맞춤형 여행 추천 서비스입니다.")
st.sidebar.write(f"현재 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
st.sidebar.write(f"현재 단계: {st.session_state.stage}/3")

# 사용 방법 안내
with st.sidebar.expander("사용 방법"):
    st.write("""
    1. 여행 취향을 입력하세요
    2. AI가 추천한 여행지 중 하나를 선택하세요
    3. 선택한 여행지의 하루 일정을 받아보세요
    4. 추가 질문이 있으면 언제든지 물어보세요
    """)

if __name__ == "__main__":
    main()
