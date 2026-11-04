from phase21_autonomous_scientist import call_muse_model

feedback_prompt = """You are an engineering scientist.
A proposed model predicted dx = 38.69 mm for F=25N, th=850um (dy=48.18mm).
FEA measured: actual dx = 11.90 mm.
Ground truth measurements:
1. F=0.5N, th=850um -> dy=2.339mm, dx=0.0468mm
2. F=1.0N, th=1050um -> dy=2.450mm, dx=0.0480mm
3. F=0.5N, th=1200um -> dy=0.850mm, dx=0.0061mm
4. F=2.0N, th=1200um -> dy=3.400mm, dx=0.0980mm

Analyze the discrepancy and revise your coefficients for:
Pi_x = C * (Pi_y ^ alpha) / (Pi_th ^ beta)
Where Pi_x = dx/L, Pi_y = dy/L, Pi_th = th/L, with L=30mm.
Respond ONLY with a single valid JSON object, no markdown, no other text:
{"falsification_analysis": "analysis text", "revised_coefficients": {"C": 0.05, "alpha": 1.8, "beta": 0.5}}"""

r = call_muse_model(feedback_prompt, temperature=0.1)
print("Parsed JSON:", r.get("parsed_json"))
print("Raw Content:", repr(r.get("content")))
