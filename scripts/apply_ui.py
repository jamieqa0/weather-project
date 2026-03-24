import sys

with open("static/about.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Insert CSS
css_insert = """
    /* Scroll Reveal */
    .reveal { opacity: 0; transform: translateY(30px); transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94); }
    .reveal.active { opacity: 1; transform: translateY(0); }
    
    /* Holographic Hover */
    .glass { transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.3s ease; }
    .hover-hologram:hover {
      transform: translateY(-5px) scale(1.02);
      box-shadow: 0 10px 40px -10px rgba(90, 248, 251, 0.15), 0 0 20px rgba(204, 151, 255, 0.1), inset 0 0 0 1px rgba(90, 248, 251, 0.2);
      background: rgba(31, 31, 35, 0.7);
    }
    
    /* Animated Data Flow Pipes */
    .pipe { width: 2px; height: 35px; background: rgba(90, 248, 251, 0.1); margin: 0.2rem auto; position: relative; overflow: hidden; }
    .pipe::before {
      content: ''; position: absolute; top: -100%; left: 0; width: 100%; height: 100%;
      background: linear-gradient(to bottom, transparent, #5af8fb, #ffe792, transparent);
      animation: pulse-flow 1.5s infinite linear;
    }
    @keyframes pulse-flow { 0% { top: -100%; } 100% { top: 100%; } }
    .pulse-node { animation: glow-pulse 2s infinite alternate; }
    @keyframes glow-pulse { 0% { box-shadow: 0 0 5px rgba(90,248,251,0.2); } 100% { box-shadow: 0 0 20px rgba(90,248,251,0.6); } }
"""
html = html.replace("    @media (max-width: 900px) {", css_insert + "\n    @media (max-width: 900px) {")

# 2. Add .reveal .hover-hologram to .glass
html = html.replace('class="glass rounded-xl p-6 text-center"', 'class="glass rounded-xl p-6 text-center reveal hover-hologram"')
html = html.replace('class="glass rounded-xl p-6"', 'class="glass rounded-xl p-6 reveal hover-hologram"')
html = html.replace('class="glass rounded-xl p-6 flex gap-4"', 'class="glass rounded-xl p-6 flex gap-4 reveal hover-hologram"')
html = html.replace('class="glass rounded-xl p-6 hover:bg-secondary/5 transition block"', 'class="glass rounded-xl p-6 hover:bg-secondary/5 transition block reveal hover-hologram"')
html = html.replace('class="glass rounded-xl p-8 overflow-x-auto"', 'class="glass rounded-xl p-8 overflow-x-auto reveal hover-hologram"')

# 3. Add .reveal to steps
html = html.replace('<div class="flex gap-6">', '<div class="flex gap-6 reveal">')

# 4. Animated Data Flow Pipes
html = html.replace('<div class="arch-arrow">↓</div>', '<div class="pipe"></div>')
branch_old = """          <div class="arch-arrow" style="display:flex;gap:3rem;justify-content:center">
            <span>↓</span><span>↓</span>
          </div>"""
branch_new = """          <div style="display:flex;gap:12rem;justify-content:center;margin:0.2rem 0">
            <div class="pipe" style="margin:0;"></div>
            <div class="pipe" style="margin:0;"></div>
          </div>"""
html = html.replace(branch_old, branch_new)

# 5. Add Node Glow to final app
html = html.replace('class="arch-node n-app"', 'class="arch-node n-app pulse-node"')

# 6. Add JS Reveal Observer
js_insert = """
      // Scroll Reveal Observer
      var revealObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('active');
          }
        });
      }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });
      document.querySelectorAll('.reveal').forEach(function(el) {
        revealObserver.observe(el);
      });
"""
html = html.replace("      ids.forEach(function (id) {", js_insert + "\n      ids.forEach(function (id) {")

with open("static/about.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Wow UI injected successfully!")
