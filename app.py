#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06届毕业20周年聚会问卷 - Flask 服务器
"""

import os
import json
import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

RESPONSES_FILE = os.path.join(DATA_DIR, "responses.json")


def load_responses():
    """加载已有回复"""
    if not os.path.exists(RESPONSES_FILE):
        return []
    with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_response(data):
    """保存一条回复"""
    responses = load_responses()
    data["id"] = len(responses) + 1
    data["submit_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    responses.append(data)
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)
    return data["id"]


@app.route("/")
def index():
    """问卷首页"""
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    """提交问卷"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "无效的提交数据"}), 400

        # 验证必填字段
        required = ["name", "phone", "classGroup", "hotel", "tour", "hasChild"]
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400

        # 如果带小孩，必须填小孩数量
        if data.get("hasChild") == "是" and not data.get("kidsCount"):
            return jsonify({"success": False, "message": "请填写带几个小孩"}), 400

        save_response(data)
        return jsonify({"success": True, "message": "提交成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/admin/responses")
def view_responses():
    """查看所有回复（管理用）"""
    responses = load_responses()
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>问卷回复管理</title>
        <style>
            body { font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f5; }
            h1 { color: #262626; }
            table { border-collapse: collapse; width: 100%; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
            th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
            th { background: #2068FF; color: #fff; font-weight: 600; }
            tr:hover { background: #f0f5ff; }
            .stats { margin: 16px 0; padding: 16px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
            .stats span { margin-right: 24px; font-size: 14px; color: #666; }
            .stats strong { color: #2068FF; font-size: 18px; }
            .btn { display: inline-block; padding: 8px 20px; background: #2068FF; color: #fff; text-decoration: none; border-radius: 6px; font-size: 14px; margin: 8px 0; }
            .btn.export { background: #52c41a; }
            @media (max-width: 600px) {
                table { font-size: 12px; }
                th, td { padding: 6px 8px; }
            }
        </style>
    </head>
    <body>
        <h1>问卷回复管理</h1>
        <div class="stats">
            <span>总回复数：<strong>""" + str(len(responses)) + """</strong></span>
            <span>最后更新：<strong>""" + (responses[-1]["submit_time"] if responses else "-") + """</strong></span>
        </div>
        <a class="btn" href="/admin/export">导出为 JSON</a>
        <a class="btn export" href="/admin/export-csv">导出为 CSV</a>
        <br><br>
    """
    if responses:
        html += """
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>提交时间</th>
                    <th>姓名</th>
                    <th>联系电话</th>
                    <th>班级</th>
                    <th>订酒店</th>
                    <th>行程</th>
                    <th>带小孩</th>
                    <th>小孩数量</th>
                    <th>特别需求</th>
                </tr>
            </thead>
            <tbody>
        """
        for r in responses:
            html += f"""
                <tr>
                    <td>{r['id']}</td>
                    <td>{r.get('submit_time', '-')}</td>
                    <td>{r['name']}</td>
                    <td>{r['phone']}</td>
                    <td>{r.get('classGroup', '-')}</td>
                    <td>{r['hotel']}</td>
                    <td>{r['tour']}</td>
                    <td>{r['hasChild']}</td>
                    <td>{r.get('kidsCount', '-') or '-'}</td>
                    <td>{r.get('special', '-') or '-'}</td>
                </tr>
            """
        html += "</tbody></table>"
    else:
        html += "<p style='color:#999;'>暂无回复数据</p>"

    html += "</body></html>"
    return html


@app.route("/admin/export")
def export_json():
    """导出 JSON"""
    responses = load_responses()
    return jsonify(responses)


@app.route("/admin/export-csv")
def export_csv():
    """导出 CSV"""
    import csv
    import io
    responses = load_responses()
    output = io.StringIO()
    writer = csv.writer(output)

    # 表头
    headers = ["编号", "提交时间", "姓名", "联系电话", "班级", "订酒店", "行程", "带小孩", "小孩数量", "特别需求"]
    writer.writerow(headers)

    for r in responses:
        writer.writerow([
            r.get("id", ""),
            r.get("submit_time", ""),
            r.get("name", ""),
            r.get("phone", ""),
            r.get("classGroup", ""),
            r.get("hotel", ""),
            r.get("tour", ""),
            r.get("hasChild", ""),
            r.get("kidsCount", ""),
            r.get("special", "")
        ])

    csv_content = output.getvalue()
    from flask import Response
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=responses.csv"}
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"问卷服务启动: http://localhost:{port}")
    print(f"管理后台: http://localhost:{port}/admin/responses")
    app.run(host="0.0.0.0", port=port)
