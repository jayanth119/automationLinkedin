document_prompt = """
You are an assistant. Create structured notes ONLY from the extracted text provided below.
Do not use external knowledge, assumptions, or interpretations beyond what is explicitly in the text.

### Input:

Post ID: {post_id}
Extracted Text:
{combined_text}

### Notes-Making Rules:
1. Headings & Hierarchy  
   - Use Markdown formatting:
     - `#` for main heading (post/topic title if present).
     - `##` for subheadings.
     - `-` for bullet points.
     - `1.` for numbered steps.

2. Code & Syntax  
   - Preserve all code blocks exactly.
   - Wrap code inside `code fences` with correct indentation and spacing.

3. Tables & Structured Data  
   - Convert tables into Markdown tables while keeping exact values.
   - Retain bullet lists, checklists, or outlines exactly as they appear.

4. Equations & Math  
   - If LaTeX is visible → keep exact LaTeX.
   - If plain math symbols → write them as-is without modification.

5. Diagrams, Charts, and Graphs (if described in text)  
   - Convert diagram-related text into structured bullet points.
   - Retain relationships/flow described in text.
   - If incomplete → mark `[incomplete]`.

6. Formatting & Completeness  
   - Maintain original order of information.
   - Mark unclear or cut-off content with `[unclear]` or `[cut-off]`.
   - Do not summarize or shorten unless explicitly written in the extracted text.

7. Final Output  
   - Produce structured notes that fully capture the extracted text.
   - Ensure reading the notes gives a complete understanding of the post without needing extra context.
"""
