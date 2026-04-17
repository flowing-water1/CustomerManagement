from dotenv import load_dotenv
import streamlit as st

from customer_management.config import Settings
from customer_management.ui.admin import render_admin_area
from customer_management.ui.sales import render_sales_area
from customer_management.ui.shared import get_session_factory

load_dotenv()

st.set_page_config(page_title="客户信息管理", layout="wide")

settings = Settings.from_sources(secrets=st.secrets)
session_factory = get_session_factory(settings.database_url)

st.title("客户信息管理")

sales_tab, admin_tab = st.tabs(["销售入口", "管理员入口"])

with sales_tab:
    render_sales_area(session_factory)

with admin_tab:
    render_admin_area(session_factory)
