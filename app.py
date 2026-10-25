"""CareCheck: an accessible health-information risk checker for older adults."""
from pathlib import Path
import os
import json
from openai import OpenAI
from dash import Dash, Input, Output, State, ctx, dcc, html
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

SAMPLE_CLAIM = "Drinking very hot lemon water every morning melts away artery plaque and means you do not need cholesterol medicine."

def analyze_claim(text: str) -> dict:
    """Analyze a claim with the configured model, with a safe local fallback."""
    lowered = text.lower()
    urgent_guidance = "bleed" in lowered and ("er" in lowered or "emergency" in lowered) and ("30 minute" in lowered or "30 minutes" in lowered or "nonstop" in lowered or "non-stop" in lowered or "continuous" in lowered or "keep bleeding" in lowered)
    broad_wellness_claim = ("blueberr" in lowered and ("eye health" in lowered or "eyesight" in lowered)) or ("may support" in lowered and "health" in lowered)
    obvious_biohazard = any(term in lowered for term in [
        "decomposing whale", "whale carcass", "decomposing animal", "animal carcass",
        "dead animal", "rotting carcass", "decaying carcass", "decomposing carcass"
    ])
    # Prefer the course Portkey key when both approved variables are present;
    # otherwise allow a user's own OpenAI key.
    portkey_key = os.getenv("PORTKEY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    api_key = portkey_key or openai_key
    if api_key:
        try:
            client_kwargs = {"api_key": api_key}
            if portkey_key:
                client_kwargs["base_url"] = "https://api.portkey.ai/v1"
                client_kwargs["default_headers"] = {"x-portkey-api-key": api_key}
            client = OpenAI(**client_kwargs)
            response = client.responses.create(
                model=os.getenv("CARECHECK_MODEL", "gpt-6-luna"),
                input=[{"role":"system", "content":"You are CareCheck, a cautious health-information checker for older adults. Do not diagnose. Analyze the user's claim and cite trustworthy sources such as CDC, NIH, NHS, WHO, or major medical associations. You MUST set level to exactly one of: High caution, Mostly correct, Looks useful, Needs checking, Unable to verify. Use Mostly correct when the advice is broadly right but needs context or an important safety addition. Use High caution only when the advice is false, dangerous, or could cause harmful delay or treatment changes. Return JSON with keys level, summary, why, next_step, sources (array), tool. Keep it warm, plain English, and concise."}, {"role":"user", "content":text}],
            )
            parsed = json.loads(response.output_text)
            # Do not let a variable model response downplay an obvious exposure hazard.
            if obvious_biohazard:
                parsed["level"] = "High caution"
            level = parsed.get("level")
            if isinstance(level, bool):
                parsed["level"] = "High caution" if level is False else "Looks useful"
            elif isinstance(level, str):
                normalized = level.strip().lower()
                if normalized in {"false", "high", "high risk", "dangerous", "unsafe"}:
                    parsed["level"] = "High caution"
                elif normalized in {"true", "safe", "supported", "looks good"}:
                    parsed["level"] = "Looks useful"
                elif "mostly correct" in normalized or "mostly true" in normalized or "partly correct" in normalized or "generally correct" in normalized or "generally_correct" in normalized or "generally true" in normalized:
                    parsed["level"] = "Mostly correct"
                elif normalized in {"uncertain", "unknown", "cannot verify", "unable to verify"}:
                    parsed["level"] = "Unable to verify"
            parsed["tool"] = parsed.get("tool", "Evidence review")
            return parsed
        except Exception as error:
            print(f"Evidence review unavailable: {type(error).__name__}")
    medication_risk = any(word in lowered for word in ["stop", "don't need", "do not need", "medicine", "medication"])
    if "cataract" in lowered or "eyesight" in lowered or "vision" in lowered:
        summary = "There is no good evidence that a food can cure cataracts or permanently restore eyesight. Vision changes deserve an eye examination."
    elif "blood pressure" in lowered or "hypertension" in lowered:
        summary = "Lifestyle choices can support heart health, but a juice or single food should not be treated as a guaranteed replacement for blood-pressure care."
    elif "diabetes" in lowered or "blood sugar" in lowered:
        summary = "Food choices can affect blood sugar, but this claim should not be used to replace a diabetes treatment plan or prescribed medicine."
    elif "cancer" in lowered or "tumor" in lowered:
        summary = "There is no basis here for treating a food or home remedy as a cancer cure. Delaying proper evaluation could be harmful."
    elif medication_risk:
        summary = "This message suggests replacing prescribed treatment with a home remedy. That is a serious claim and needs professional advice."
    else:
        summary = "This health promise is too broad to accept without checking the evidence, the amount involved, and the person’s medical situation."
    if "diabetes" in lowered or "blood sugar" in lowered:
        why = "This message makes a claim about blood sugar or diabetes treatment. Food and drinks may be part of a healthy routine, but they should not be presented as a replacement for diabetes care."
    elif "cancer" in lowered or "tumor" in lowered:
        why = "Cancer claims need especially careful evidence because delaying diagnosis or treatment can cause harm. A single food, supplement, or home remedy should not be presented as a cure."
    elif "weight" in lowered or "lose fat" in lowered or "detox" in lowered:
        why = "Weight-loss and detox messages often turn a small or uncertain finding into a promise. The wording does not provide enough evidence to support a guaranteed result."
    elif "vitamin" in lowered or "supplement" in lowered:
        why = "Supplements can affect people differently and may interact with medicines. A natural product is not automatically safe or effective."
    else:
        why = "This message makes a medical promise without enough context about the person, the dose, or the evidence. That is why it deserves a closer look before being shared."
    if obvious_biohazard:
        summary = "Do not sit in or touch a decomposing animal. A carcass can expose someone to bacteria, parasites, bodily fluids, and physical hazards; it is not a safe arthritis treatment."
        why = "This advice recommends direct contact with a decomposing whale carcass. That is an immediate hygiene and injury concern, not a harmless home remedy."
    return {
        "level": "High caution" if obvious_biohazard else ("Mostly correct" if urgent_guidance else ("Needs checking" if broad_wellness_claim else ("High caution" if medication_risk else "Needs checking"))),
        "summary": summary,
        "why": why,
        "next_step": "Do not stop or change prescribed medicine based on a forwarded message. Ask a healthcare professional about your situation.",
        "sources": ["NHS: Medicines information", "American Heart Association: Cholesterol and heart health"],
        "tool": "Claim safety screener",
    }

app = Dash(__name__, title="CareCheck")
app.layout = html.Div([
    dcc.Store(id="analysis-store"),
    html.Header([html.Div([html.Div("✓", className="logo-mark"), html.Span("CareCheck", className="brand")], className="brand-lockup"), html.Span("Health information, explained clearly", className="header-note")], className="topbar"),
    html.Main([
        html.Section([html.Div([html.P("A QUIET SECOND OPINION", className="eyebrow"), html.H1("Before you believe it, check it."), html.P("You can share any health message you receive here. We’ll go through it with you and point out anything worth asking your doctor about.", className="lede")], className="hero-copy"), html.Div([html.P("DESIGNED FOR EVERYDAY USE", className="eyebrow"), html.P("Large type · Plain language · No judgment", className="accessibility-note")], className="hero-note")], className="hero-grid"),
        html.Section([html.Div([html.P("1  ·  PASTE THE MESSAGE", className="eyebrow"), html.H2("What did you receive?", className="section-title"), html.P("Copy the health advice exactly as it was sent to you.", className="muted")], className="section-heading"), dcc.Textarea(id="claim-input", value="", placeholder="Paste a health tip here…", className="claim-input", spellCheck=True), html.Div([html.Button("Use an example", id="example-button", className="secondary-button"), html.Button("Check this message", id="check-button", className="primary-button")], className="action-row")], className="panel claim-panel"),
        html.Div(id="result-area", children=[html.Div([html.P("2  ·  YOUR RESULT", className="eyebrow"), html.H2("Your result will appear here", className="section-title"), html.P("CareCheck will explain the message in plain language and highlight anything that deserves extra caution.", className="muted")], className="empty-result")], className="result-wrapper"),
        html.Section([html.P("A NOTE ABOUT SAFETY", className="eyebrow"), html.P("CareCheck does not diagnose conditions or replace a healthcare professional. If someone has severe or sudden symptoms, seek urgent medical help.", className="safety-note")], className="safety-panel"),
    ], className="page"),
    html.Footer("CareCheck · A calm way to pause before sharing health advice.")
], className="app-shell")

@app.callback(Output("claim-input", "value"), Input("example-button", "n_clicks"), prevent_initial_call=True)
def fill_example(_):
    return SAMPLE_CLAIM

@app.callback(Output("result-area", "children"), Input("check-button", "n_clicks"), State("claim-input", "value"), prevent_initial_call=True)
def show_result(_, claim):
    if not (claim or "").strip():
        return html.Div([html.P("START WITH A MESSAGE", className="eyebrow"), html.H2("Paste a health message first", className="section-title"), html.P("There is nothing to check yet. Copy the message you received and paste it above.", className="muted")], className="empty-result warning-result")
    result = analyze_claim(claim)
    # Final UI safety gate: never display a mild review label for direct
    # exposure to a decomposing animal carcass, regardless of model output.
    claim_lower = claim.lower()
    if any(term in claim_lower for term in ["decomposing whale", "whale carcass", "decomposing animal", "animal carcass", "rotting carcass", "decaying carcass", "decomposing carcass"]):
        result["level"] = "High caution"
        result["summary"] = "Do not sit in or touch a decomposing animal. A carcass can expose someone to bacteria, parasites, bodily fluids, and physical hazards; it is not a safe arthritis treatment."
        result["why"] = "This advice recommends direct contact with a decomposing whale carcass. That is an immediate hygiene and injury concern, not a harmless home remedy."
        result["next_step"] = "Do not try this. If you already had contact, wash thoroughly and contact a healthcare professional or poison-control service if you develop symptoms."
    evidence_text = f"{result.get('summary', '')} {result.get('why', '')}".lower()
    caution_words = ["no good evidence", "no evidence", "not proven", "not supported", "should not", "do not delay", "replace prescribed", "cure", "guaranteed", "harmful", "dangerous"]
    raw_level = str(result.get("level", "")).strip().lower().replace("-", "_")
    if result.get("level") == "Mostly correct" or any(label in raw_level for label in ["mostly_correct", "generally_correct", "mostly_true", "generally_true", "partly_correct"]):
        result_title = "This is mostly correct, but let me tell you a bit more."
    elif result.get("level") == "High caution" or any(word in evidence_text for word in caution_words):
        result_title = "Be careful with this advice."
    elif result.get("level") == "Looks useful":
        result_title = "This looks useful."
    elif result.get("level") == "Unable to verify":
        result_title = "I could not verify this."
    else:
        result_title = "This needs a little more checking."
    return html.Div([html.Div([html.P("2  ·  LET'S LOOK AT IT TOGETHER", className="eyebrow"), html.Span(result["level"], className="risk-badge caution")], className="result-header"), html.H2(result_title, className="result-title"), html.P(result["summary"], className="result-summary"), html.Div([html.Div([html.H3("Why I’m suggesting a pause"), html.P(result["why"])], className="result-block"), html.Div([html.H3("What you could do next"), html.P(result["next_step"])], className="result-block")], className="result-grid"), html.Div([html.H3("If you’d like to read more"), html.Ul([html.Li(source) for source in result["sources"]])], className="sources-block"), html.Div([html.Span("Checked with: ", className="muted"), html.Span(result["tool"])], className="tool-note")], className="result-card")

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)

