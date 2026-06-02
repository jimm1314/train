"""
倒计时组件
支持启动倒计时，时间到后显示提醒。
"""
import streamlit as st
import streamlit.components.v1 as components


def render_timer(minutes: int, trigger_key: int):
    """
    渲染一个 HTML 倒计时器。
    trigger_key 变化时会重新启动倒计时。
    """
    html_code = f"""
    <div id="timer_display_{trigger_key}" style="
        font-size: 24px;
        font-weight: bold;
        color: #ff4b4b;
        background-color: #fef2f2;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #fca5a5;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.15);
    ">
        ⏳ 准备就绪...
    </div>
    <script>
    var time_left = {minutes} * 60;
    var display = document.getElementById("timer_display_{trigger_key}");
    clearInterval(window.my_timer_{trigger_key});

    window.my_timer_{trigger_key} = setInterval(function() {{
        var m = Math.floor(time_left / 60);
        var s = time_left % 60;
        m = m < 10 ? "0" + m : m;
        s = s < 10 ? "0" + s : s;

        display.innerHTML = "⏱️ 倒计时: " + m + " 分 " + s + " 秒";
        time_left--;

        if (time_left < 0) {{
            clearInterval(window.my_timer_{trigger_key});
            display.innerHTML = "⏰ 时间到！请停止作答！";
            display.style.color = "white";
            display.style.backgroundColor = "#ef4444";
            display.style.animation = "pulse 1s infinite";
        }}
    }}, 1000);
    </script>
    """
    components.html(html_code, height=70)
