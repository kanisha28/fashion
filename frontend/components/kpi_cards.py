import streamlit as st
from typing import Optional


def render_kpi_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
    sub_text: Optional[str] = None,
    icon: Optional[str] = None
):
    """
    Renders an ultra-modern, glassmorphism KPI card.
    Carefully formatted without 4-space markdown indentations to prevent code block parsing.
    """
    delta_html = ""
    if delta:
        badge_bg = "rgba(16, 185, 129, 0.15)" if delta_color == "green" else ("rgba(239, 68, 68, 0.15)" if delta_color == "red" else "rgba(99, 102, 241, 0.15)")
        badge_color = "#10B981" if delta_color == "green" else ("#F87171" if delta_color == "red" else "#818CF8")
        delta_html = f'<div style="margin-top: 8px;"><span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_color}44; font-size: 0.8rem; font-weight: 600; padding: 3px 10px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 4px;">{delta}</span></div>'

    sub_html = ""
    if sub_text:
        sub_html = f'<div style="font-size: 0.78rem; color: #94A3B8; margin-top: 6px; font-weight: 500;">{sub_text}</div>'

    icon_html = f'<span style="font-size: 1.25rem;">{icon}</span>' if icon else ""
    help_attr = f' title="{help_text}" style="cursor: help; color: #64748B; font-size: 0.85rem;"' if help_text else ' style="display: none;"'

    card_html = f"""<div style="background: linear-gradient(135deg, rgba(23, 37, 68, 0.75) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 20px 22px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08); position: relative; overflow: hidden; backdrop-filter: blur(16px); min-height: 155px; display: flex; flex-direction: column; justify-content: space-between;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div style="color: #94A3B8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; display: flex; align-items: center; gap: 6px;">
{icon_html}
<span>{title}</span>
</div>
<span{help_attr}>ℹ️</span>
</div>
<div style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em; margin-top: 6px; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">
{value}
</div>
{delta_html}
{sub_html}
</div>"""

    st.markdown(card_html, unsafe_allow_html=True)
