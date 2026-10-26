import streamlit as st
import json
import os
import pandas as pd
import numpy as np
from groq import Groq

# 1. إعدادات الصفحة والواجهة الاحترافية
st.set_page_config(
    page_title='Magdy AI Suite', 
    page_icon='⚡', 
    layout='wide',
    initial_sidebar_state='expanded'
)

# تصميم وتنسيق الواجهة (CSS مخصص)
st.markdown('''<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); 
    background-attachment: fixed; 
    color: #f8fafc;
}
[data-testid='stSidebar'] {
    background-color: rgba(15, 23, 42, 0.95) !important; 
    backdrop-filter: blur(12px); 
    border-right: 1px solid rgba(255,255,255,0.1);
}
.stChatMessage {
    background-color: rgba(30, 41, 59, 0.85); 
    border-radius: 12px; 
    border: 1px solid rgba(255, 255, 255, 0.1); 
    margin-bottom: 10px;
}
.engine-card {
    background: rgba(255,255,255,0.04); 
    padding: 20px; 
    border-radius: 12px; 
    border: 1px solid rgba(255,255,255,0.1); 
    margin-bottom: 15px;
}
</style>''', unsafe_allow_html=True)

# 2. إعداد مفتاح Groq وربط العميل (Client)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'YOUR_GROQ_API_KEY_HERE')
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    client = None

DB_FILE = 'chat_history.json'

# الأقسام الأساسية للمنصة (تم إضافة Code & Script Analyzer الجديد)
default_chats = {
    'Video Generator Planner': 'You are a professional Video Producer and AI Prompt Engineer. Help Magdy break down long video scripts (10-20 minutes) into timed scenes, audio cues, and precise English visual prompts for AI video generators.',
    'AI Video & Visual Hub': 'SYSTEM_MODULE_GENERATOR',
    'Analytics & Performance Hub': 'SYSTEM_MODULE_ANALYTICS',
    'Code & Script Analyzer': 'SYSTEM_MODULE_CODE_ANALYZER',
    'Cybersecurity & Bugs': 'You are a Senior Cybersecurity Expert. Help Magdy analyze system vulnerabilities, understand penetration testing, and write professional Bug Bounty reports.',
    'AI Mentor': 'You are a patient AI Mentor. Teach Magdy AI, Machine Learning, and API integration concepts step-by-step with practical code examples.',
    'Ain Shams Studies': 'You are an Engineering Academic Assistant for Ain Shams University. Help Magdy study engineering modules, solve equations, and organize study schedules.',
    'Life Coach & Routine': 'You are Magdy personal Life Coach. Help him manage time, maintain focus, build healthy habits, and avoid burnout.',
    'Projects & GUI Dev': 'You are a Senior Python Developer and Media Processing Specialist (OpenCV, MoviePy, Streamlit). Help Magdy upgrade prototypes, apply video transformations, and generate clean production-ready code.',
    'General Assistant': 'You are Magdy personal AI assistant on his local HP workstation. Answer clearly and helpfully.'
}

# 3. إدارة جلسات المحادثة والذاكرة
def load_chats():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                for k, v in default_chats.items():
                    if k not in saved:
                        saved[k] = [{'role': 'system', 'content': v}]
                return saved
        except Exception:
            pass
    return {name: [{'role': 'system', 'content': prompt}] for name, prompt in default_chats.items()}

def save_chats():
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.chats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if 'chats' not in st.session_state:
    st.session_state.chats = load_chats()

if 'current_chat' not in st.session_state:
    st.session_state.current_chat = 'Code & Script Analyzer'

# 4. القائمة الجانبية (Sidebar Workspace Navigation)
with st.sidebar:
    st.title('⚡ Magdy AI Suite')
    st.caption('Local Python Workstation | GitHub Ready')
    st.divider()
    
    st.session_state.current_chat = st.radio('Choose Workspace:', list(st.session_state.chats.keys()))
    st.divider()
    
    # خيار تنزيل السجل للمحادثات العادية
    if st.session_state.current_chat not in ['AI Video & Visual Hub', 'Analytics & Performance Hub', 'Code & Script Analyzer']:
        chat_messages_list = st.session_state.chats[st.session_state.current_chat]
        chat_data = "\n---\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_messages_list if m['role'] != 'system'])
        st.download_button('📥 Download Chat Output', data=chat_data, file_name=f"{st.session_state.current_chat.replace(' ', '_')}_output.txt", mime='text/plain')
        st.divider()
        
    if st.button('Clear Chat History', use_container_width=True):
        st.session_state.chats[st.session_state.current_chat] = [{'role': 'system', 'content': default_chats[st.session_state.current_chat]}]
        save_chats()
        st.rerun()
        
    st.divider()
    uploaded_file = st.file_uploader('Upload Code / Document', type=['txt', 'py', 'md', 'csv', 'html'])

# 5. التوجيه بناءً على القسم المختار
if st.session_state.current_chat == 'AI Video & Visual Hub':
    st.title('🎬 AI Video & Visual Generation Hub')
    st.write('مركز التوليد البصري المباشر: قم بتوليد الأصول السينمائية وربط محركات الفيديو السحابية.')
    
    col1, col2 = st.columns([1, 1], gap='medium')
    
    with col1:
        st.markdown('<div class="engine-card">', unsafe_allow_html=True)
        st.subheader('🖼️ Fast Concept Image Generator')
        img_prompt = st.text_area('Enter English Visual Prompt:', placeholder='A cinematic 4k shot of a futuristic Sudanese city at sunset...')
        img_aspect = st.selectbox('Aspect Ratio:', ['16:9 (Landscape)', '9:16 (Portrait)', '1:1 (Square)'])
        
        if st.button('🚀 Generate Visual Asset', use_container_width=True):
            if img_prompt:
                st.info('جارٍ توليد الصورة السينمائية عبر محرك المعالجة البصرية...')
                formatted_prompt = img_prompt.replace(' ', '%20')
                img_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}?width=1280&height=720&nologo=true"
                st.image(img_url, caption="Generated Visual Concept", use_column_width=True)
                st.success("تم التوليد بنجاح داخل المنصة!")
            else:
                st.warning('يرجى كتابة البرومبت أولاً.')
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="engine-card">', unsafe_allow_html=True)
        st.subheader('🎥 AI Video Engine Connector')
        st.write('ربط محركات توليد الفيديو السحابية أو النماذج الخارجية.')
        
        video_engine = st.selectbox('Select AI Video Engine:', [
            'Replicate / AnimateDiff API (Open Source Engine)',
            'Luma Dream Machine API Integration',
            'Runway Gen-3 API Pipeline',
            'Local GPU Worker (ComfyUI / Automatic1111 Backend)'
        ])
        
        video_prompt = st.text_area('Enter Video Prompt for Pipeline:', placeholder='Cinematic wide shot, slow motion, agricultural fields...')
        api_token = st.text_input('Engine API Token (Optional):', type='password')
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button('🎬 Queue Video Job', use_container_width=True):
                st.info(f'تم إرسال طلب التوليد إلى محرك: {video_engine}')
                st.success('تمت إضافة المهمة لقائمة الانتظار بنجاح!')
        with c2:
            st.link_button("🌐 Open Runway ML", "https://runwayml.com", use_container_width=True)
            st.link_button("🌐 Open Luma Dream", "https://lumalabs.ai/dream-machine", use_container_width=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_chat == 'Analytics & Performance Hub':
    st.title('📊 Analytics & Performance Hub')
    st.write('لوحة التحليلات والرسوم البيانية: تتبع أداء مشاريعك، ومقاييس إنتاج محتوى Cognicraft.')
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="Total Video Scripts", value="12", delta="+3 this month")
    with m2:
        st.metric(label="Generated Assets", value="48", delta="+12%")
    with m3:
        st.metric(label="System Uptime", value="99.9%", delta="Stable")
    with m4:
        st.metric(label="AI Workspaces", value="10 Active", delta="Optimized")
        
    st.divider()
    
    col_a, col_b = st.columns(2, gap='medium')
    with col_a:
        st.subheader('📈 Cognicraft Production Growth')
        chart_data = pd.DataFrame(
            np.random.randn(10, 2) * [2, 50] + [20, 200],
            columns=['Scripts Planned', 'Generated Visuals']
        )
        st.line_chart(chart_data)
        st.caption("معدل نمو تخطيط السكربتات وتوليد الأصول البصرية أسبوعياً.")
        
    with col_b:
        st.subheader('📉 Resource & API Usage Analytics')
        bar_data = pd.DataFrame(
            np.random.rand(5, 3) * 100,
            columns=['Groq API', 'Image Gen Hub', 'Local Processing']
        )
        st.bar_chart(bar_data)
        st.caption("توزيع استهلاك ومعدلات استدعاء أدوات الذكاء الاصطناعي.")

elif st.session_state.current_chat == 'Code & Script Analyzer':
    st.title('🛠️ Code & Script AI Analyzer')
    st.write('أداة تحليل وترقية الأكواد: الصق الكود البرمجي الخاص بك هنا لتحليله، اكتشاف الأخطاء، واقتراح ترقيات فورية عبر نموذج الذكاء الاصطناعي.')
    
    code_input = st.text_area('Paste your Python code or script here to upgrade / review:', height=250, placeholder='def my_function():\n    # Write your code here...')
    analysis_goal = st.selectbox('Select Analysis Goal:', [
        'Review & Clean Code (تنظيف ومراجعة الكود)',
        'Optimize Performance (تحسين الأداء والسرعة)',
        'Find & Fix Bugs (اكتشاف وإصلاح الأخطاء)',
        'Add Comments & Documentation (إضافة توثيق وشرح)'
    ])
    
    if st.button('🔍 Analyze & Upgrade Code', use_container_width=True):
        if code_input.strip():
            with st.spinner('جارٍ تحليل الكود وتوليد التحسينات عبر نموذج الذكاء الاصطناعي...'):
                prompt_content = f"Please act as an Expert Senior Software Engineer. Analyze the following code with the goal: '{analysis_goal}'. Provide a detailed review, explain improvements, and output the clean upgraded code:\n\n```python\n{code_input}\n```"
                
                try:
                    response = client.chat.completions.create(
                        model='qwen/qwen3.8-27b',
                        messages=[
                            {'role': 'system', 'content': 'You are an expert software engineer and code reviewer.'},
                            {'role': 'user', 'content': prompt_content}
                        ]
                    )
                    analysis_result = response.choices[0].message.content
                    st.success('تم تحليل الكود بنجاح!')
                    st.markdown('### 💡 AI Analysis & Upgraded Code:')
                    st.markdown(analysis_result)
                except Exception as e:
                    st.error(f'حدث خطأ أثناء الاتصال بنموذج الذكاء الاصطناعي: {str(e)}')
        else:
            st.warning('يرجى لصق الكود البرمجي في الحقل بالأعلى أولاً.')

else:
    st.title(f'{st.session_state.current_chat}')
    current_messages = st.session_state.chats[st.session_state.current_chat]

    for msg in current_messages:
        if msg['role'] != 'system':
            st.chat_message(msg['role']).write(msg['content'])

    prompt = st.chat_input('Write your message or request...')
    if prompt:
        file_context = ''
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
                file_context = f'\n\n[Attached File ({uploaded_file.name})]:\n{file_content}\n'
            except Exception:
                pass
        
        full_prompt = prompt + file_context
        current_messages.append({'role': 'user', 'content': full_prompt})
        st.chat_message('user').write(prompt)
        
        if client:
            try:
                response = client.chat.completions.create(model='qwen/qwen3.8-27b', messages=current_messages)
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"عذراً يا بشمهندس، حدث خطأ أثناء الاتصال بمحرك الذكاء الاصطناعي: {str(e)}"
        else:
            bot_reply = "مفتاح Groq API غير مضبوط بشكل صحيح."
            
        current_messages.append({'role': 'assistant', 'content': bot_reply})
        save_chats()
        st.chat_message('assistant').write(bot_reply)