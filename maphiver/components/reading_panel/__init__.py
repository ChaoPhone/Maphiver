import streamlit.components.v1 as components
from typing import Optional, Tuple


def create_reading_panel(
    content: str,
    height: int = 600,
    key: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    html_code = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #fff;
        }}
        .content-container {{
            padding: 16px;
            line-height: 1.8;
            font-size: 15px;
            color: #333;
        }}
        .content-container h1, .content-container h2, .content-container h3 {{
            color: #1a1a1a;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        .content-container p {{
            margin: 0.8em 0;
        }}
        .content-container code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        .content-container pre {{
            background: #f8f8f8;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        .content-container blockquote {{
            border-left: 4px solid #4CAF50;
            margin: 1em 0;
            padding-left: 16px;
            color: #555;
            background: #f9f9f9;
            padding: 8px 16px;
            border-radius: 0 4px 4px 0;
        }}
        .content-container ul, .content-container ol {{
            padding-left: 24px;
        }}
        .content-container li {{
            margin: 0.4em 0;
        }}
        .content-container table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        .content-container th, .content-container td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        .content-container th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        .selection-toolbar {{
            position: absolute;
            display: none;
            z-index: 1000;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 4px;
            border: 1px solid #e0e0e0;
        }}
        .selection-toolbar.visible {{
            display: flex;
            gap: 4px;
        }}
        .toolbar-btn {{
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        .toolbar-btn.primary {{
            background: #4CAF50;
            color: white;
        }}
        .toolbar-btn.primary:hover {{
            background: #45a049;
        }}
        .toolbar-btn.secondary {{
            background: #f5f5f5;
            color: #333;
        }}
        .toolbar-btn.secondary:hover {{
            background: #e0e0e0;
        }}
        .quick-btn {{
            padding: 4px 8px;
            font-size: 12px;
        }}
        .selection-info {{
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="content-container" id="content">{content}</div>
    <div class="selection-toolbar" id="toolbar">
        <button class="toolbar-btn primary" onclick="askQuestion()">🤖 向AI提问</button>
        <button class="toolbar-btn secondary quick-btn" onclick="quickAsk('详细')">详细</button>
        <button class="toolbar-btn secondary quick-btn" onclick="quickAsk('简化')">简化</button>
        <button class="toolbar-btn secondary quick-btn" onclick="quickAsk('类比')">类比</button>
        <button class="toolbar-btn secondary quick-btn" onclick="quickAsk('举例')">举例</button>
    </div>
    <div class="selection-info" id="selectionInfo"></div>
    
    <script>
        let selectedText = '';
        let currentQuickType = '';
        
        document.addEventListener('mouseup', handleSelection);
        document.addEventListener('touchend', handleSelection);
        
        function handleSelection(e) {{
            setTimeout(() => {{
                const selection = window.getSelection();
                const text = selection.toString().trim();
                
                if (text.length > 0) {{
                    selectedText = text;
                    showToolbar(selection);
                }} else {{
                    hideToolbar();
                }}
            }}, 10);
        }}
        
        function showToolbar(selection) {{
            const toolbar = document.getElementById('toolbar');
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            const firstLineRect = getFirstLineRect(range);
            
            toolbar.classList.add('visible');
            
            const containerWidth = window.innerWidth;
            let left = firstLineRect.right + 10;
            
            if (left + toolbar.offsetWidth > containerWidth - 20) {{
                left = firstLineRect.left - toolbar.offsetWidth - 10;
            }}
            
            if (left < 10) {{
                left = firstLineRect.right + 10;
            }}
            
            toolbar.style.left = Math.max(10, Math.min(left, containerWidth - toolbar.offsetWidth - 10)) + 'px';
            toolbar.style.top = (firstLineRect.top + window.scrollY) + 'px';
        }}
        
        function getFirstLineRect(range) {{
            const rects = range.getClientRects();
            if (rects.length > 0) {{
                let topMost = rects[0];
                for (let i = 1; i < rects.length; i++) {{
                    if (rects[i].top < topMost.top) {{
                        topMost = rects[i];
                    }}
                }}
                return topMost;
            }}
            return range.getBoundingClientRect();
        }}
        
        function hideToolbar() {{
            const toolbar = document.getElementById('toolbar');
            toolbar.classList.remove('visible');
        }}
        
        function askQuestion() {{
            if (selectedText) {{
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: {{
                        selectedText: selectedText,
                        action: 'ask'
                    }}
                }}, '*');
                hideToolbar();
            }}
        }}
        
        function quickAsk(type) {{
            if (selectedText) {{
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: {{
                        selectedText: selectedText,
                        action: 'quick',
                        quickType: type
                    }}
                }}, '*');
                hideToolbar();
            }}
        }}
        
        document.addEventListener('click', (e) => {{
            const toolbar = document.getElementById('toolbar');
            if (!toolbar.contains(e.target) && !window.getSelection().toString().trim()) {{
                hideToolbar();
            }}
        }});
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                hideToolbar();
            }}
        }});
        
        renderMathInElement(document.getElementById('content'), {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\[', right: '\\]', display: true}},
                {{left: '\\(', right: '\\)', display: false}}
            ],
            throwOnError: false
        }});
    </script>
</body>
</html>'''
    
    result = components.html(html_code, height=height, scrolling=True)
    
    if result is None:
        return None
    
    try:
        if hasattr(result, '__getitem__'):
            return dict(result) if not isinstance(result, dict) else result
        return result
    except:
        return None