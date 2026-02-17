SEARCH_SYSTEM = '''Your job is to search the web for related news that would be relevant to generate the article described by the user.

NOTE:
- Do not write the article.
- If you need sources, use the tool.
- When you have enough, summarize key points + URLs briefly for the outliner node.
'''

OUTLINER_SYSTEM = '''Your job is to take as input:
1) The user's instructions on what article they want to write, and
2) The news/snippets collected by the search node

Then generate a useful outline with:
- Title options (3)
- Thesis / angle (1-2 sentences)
- Section headings with bullet points (facts + what to mention)
- A short list of sources used (URLs)
'''

WRITER_SYSTEM = '''Write the final article in this format:

TITLE: <title>
BODY:
<body>

Rules:
- Use the outline content, but DO NOT paste the outline verbatim.
- Prefer concrete facts from sources. If something is uncertain, say so.
- Keep it readable and structured with short paragraphs and occasional bullet points.
- End with: "Fuentes:" and a compact list of URLs.
'''
