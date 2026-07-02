import pytest
from advance_hackgpt import EnterpriseHackGPT, EnterpriseWebDashboard

def test_enterprise_web_dashboard_initialization():
    app_instance = EnterpriseHackGPT()
    dashboard = EnterpriseWebDashboard(app_instance)
    assert dashboard.hackgpt == app_instance
    assert dashboard.app is not None
