# 导入Streamlit库，所有前端界面全靠这个库的Python函数实现，不用写HTML/CSS/JS
import streamlit as st

# ========== 前端界面：纯Python就能写 ==========
# 页面标题
st.title("我的第一个Streamlit应用")
# 文本说明
st.write("这是我用GitHub+Streamlit部署的第一个网页，零前端基础也能做！")

# 前端输入框：让用户输入内容
name = st.text_input("请输入你的名字：")
# 前端按钮：点击触发动作
if st.button("点击打招呼"):
    # 点击按钮后，在页面上显示内容
    st.success(f"你好呀，{name}！🎉 恭喜你成功部署了自己的Streamlit应用")

# 额外的前端交互组件：滑块，试试实时交互
age = st.slider("选择你的年龄", 0, 100, 18)
st.write(f"你选择的年龄是：{age}")