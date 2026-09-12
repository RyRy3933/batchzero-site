# Page bodies for the Batch Zero site. Each entry: (out_path, title, description, body_html, canonical_path)

HOME = """
<section class="hero">
  <div class="hero-bg" aria-hidden="true">
    <video autoplay muted playsinline preload="metadata" poster="/assets/media/hero-poster.jpg">
      <source src="/assets/media/hero-intro.webm" type="video/webm"><source src="/assets/media/hero-intro.mp4" type="video/mp4">
    </video>
  </div>
  <div class="wrap">
    <div class="hero-copy">
      <span class="label rv">Cohort 01 · applications open</span>
      <h1 class="rv rv-d1">The accelerator for founders who haven't <span class="accent">graduated</span> yet.</h1>
      <p class="lede rv rv-d2">Batch Zero takes five high-school startups per cohort, pairs each one with two mentors for eight weeks, and puts them in front of investors at an online Demo Day. You already shipped something. We help you make it real.</p>
      <div class="hero-actions rv rv-d3">
        <a class="btn btn-primary btn-lg btn-bracket" href="/apply/founders/">I'm a founder — apply <span class="arr">→</span></a>
        <a class="btn btn-ghost btn-lg" href="/partners/">I'm a business partner <span class="arr">→</span></a>
      </div>
      <p class="dim" style="font-size:14px;margin-top:-10px">Investor, sponsor company, or mentor? <a href="/partners/" style="color:var(--accent-2)">Pick your door →</a> &nbsp;·&nbsp; <a href="/program/" style="color:var(--accent-2)">See the 8-week program</a></p>
      <div class="hero-meta rv rv-d4">
        <div><span class="k">Per cohort</span><span class="v">05 startups</span></div>
        <div><span class="k">Length</span><span class="v">08 weeks</span></div>
        <div><span class="k">Cost to founders</span><span class="v">$0</span></div>
        <div><span class="k">Applications close in</span><span class="v mono" data-countdown><span data-d>--</span>d <span data-h>--</span>h <span data-m>--</span>m <span data-s>--</span>s</span></div>
      </div>
    </div>
    <div class="hero-visual rv rv-d2">
      <div class="hud">
        <div class="hud-ring"></div>
        <video autoplay muted playsinline preload="auto" poster="/assets/media/hero-poster.jpg">
          <source src="/assets/media/hero-intro.webm" type="video/webm"><source src="/assets/media/hero-intro.mp4" type="video/mp4">
        </video>
        <span class="hud-corner tl"></span><span class="hud-corner tr"></span><span class="hud-corner bl"></span><span class="hud-corner br"></span>
        <span class="hud-tag a"><span class="blink"></span>network / live</span>
        <span class="hud-tag c">founders · mentors · capital</span>
        <span class="hud-tag b">cohort_01 · 2026</span>
      </div>
    </div>
  </div>
</section>

<div class="ticker" aria-hidden="true">
  <div class="ticker-track">
    <span><i>//</i>Apply with a startup you've already started</span><span><i>//</i>5 startups per cohort</span><span><i>//</i>2 mentors per team</span><span><i>//</i>8 weeks</span><span><i>//</i>Online Demo Day</span><span><i>//</i>Judged in-app</span><span><i>//</i>Investor access</span><span><i>//</i>Sponsor a cohort</span><span><i>//</i>Free for founders</span>
    <span><i>//</i>Apply with a startup you've already started</span><span><i>//</i>5 startups per cohort</span><span><i>//</i>2 mentors per team</span><span><i>//</i>8 weeks</span><span><i>//</i>Online Demo Day</span><span><i>//</i>Judged in-app</span><span><i>//</i>Investor access</span><span><i>//</i>Sponsor a cohort</span><span><i>//</i>Free for founders</span>
  </div>
</div>

<section id="why">
  <div class="wrap">
    <div class="section-head">
      <span class="label rv">Why this exists</span>
      <h2 class="rv rv-d1">Not a competition. Not a summer camp. A batch.</h2>
      <p class="lede rv rv-d2">College accelerators won't take you. Most "youth entrepreneurship" programs are one-off pitch contests. Batch Zero is built for the students who already have users, revenue, or a working product — and need what real founders get: structure, mentors, and a room full of people who can fund and hire them.</p>
    </div>
    <div class="grid cols-3">
      <div class="card rv"><div class="idx"><span>01</span><span>filter</span></div><h3>Post-idea only</h3><p>You need to have <em>started</em> something. A live product, a prototype with users, a first customer. Ideas alone don't get in — that filter is the whole brand.</p></div>
      <div class="card rv rv-d1"><div class="idx"><span>02</span><span>cadence</span></div><h3>Rolling cohorts</h3><p>Up to six application windows a year. Miss one, apply to the next. Every cohort is five teams, so the signal of getting in actually means something.</p></div>
      <div class="card rv rv-d2"><div class="idx"><span>03</span><span>network</span></div><h3>Three-sided from day one</h3><p>Founders, capital, and hiring in the same place. Being selected is a credential that travels — to investors, to companies, to your college application.</p></div>
    </div>
  </div>
</section>

<section id="how">
  <div class="wrap">
    <div class="section-head">
      <span class="label rv">How it works</span>
      <h2 class="rv rv-d1">Apply. Get picked. Build for eight weeks. Pitch.</h2>
    </div>
    <div class="steps rv">
      <div class="step"><span class="n">01</span><span class="t">Weeks −4 → 0</span><h3>Apply</h3><p>A short form, a 60-second video, and proof you shipped: a link, a demo, a screenshot of your first sale.</p></div>
      <div class="step"><span class="n">02</span><span class="t">2 weeks</span><h3>Review</h3><p>Every application is scored on a fixed rubric — problem, traction, team, coachability, ambition. Top five are in. Everyone else gets written feedback.</p></div>
      <div class="step"><span class="n">03</span><span class="t">8 weeks</span><h3>Program</h3><p>Two mentors per team, weekly sessions, a milestone tracker, guest office hours, and a cohort that keeps you honest.</p></div>
      <div class="step"><span class="n">04</span><span class="t">Week 8</span><h3>Demo Day</h3><p>Online pitch to a judging panel and an audience of investors and companies. Scores land in-app. One team takes the prize.</p></div>
    </div>
  </div>
</section>

<section id="doors">
  <div class="wrap">
    <div class="section-head">
      <span class="label rv">Two doors in</span>
      <h2 class="rv rv-d1">Which one are you?</h2>
    </div>
    <div class="paths">
      <a class="path rv" href="/apply/founders/">
        <span class="who">Founders</span>
        <h3>I'm a high-school founder.</h3>
        <p>You've already started something — users, revenue, a live product. Apply to the next cohort: five spots, two mentors, eight weeks, Demo Day. Free, always.</p>
        <span class="path-cta btn btn-primary">Apply as a founder <span class="arr">→</span></span>
        <span class="path-meta">10-minute application · 1 link · 1 short video</span>
      </a>
      <a class="path rv rv-d1" href="/partners/">
        <span class="who">Business partners</span>
        <h3>I want to back them.</h3>
        <p>Investors who want to see the cohort first, companies that sponsor a prize and meet the builders early, and operators who mentor a team for two months.</p>
        <span class="path-cta btn btn-ghost">Partner with Batch Zero <span class="arr">→</span></span>
        <span class="path-meta">Investors · Sponsor companies · Mentors</span>
      </a>
    </div>
  </div>
</section>

<section id="demo-day">
  <div class="wrap">
    <div class="demo">
      <div class="section-head" style="margin:0">
        <span class="label rv">Demo Day</span>
        <h2 class="rv rv-d1">Scored in the open. Judged in the app.</h2>
        <p class="lede rv rv-d2">Every cohort ends with a live, online Demo Day. Teams pitch for five minutes, judges score on a fixed rubric inside Batch Zero, and the results are visible the moment the last vote lands. Investors and companies watch live. The winner takes a sponsor-funded prize; every team leaves with feedback they can act on.</p>
        <div class="hero-actions rv rv-d3"><a class="btn btn-ghost" href="/partners/">Watch the next Demo Day →</a></div>
      </div>
      <div class="scorecard rv">
        <div class="hd"><span>demo_day / cohort_01</span><span>judge 3 of 5</span></div>
        <div class="row"><span>Problem &amp; insight</span><span class="bar"><i style="--w:88%"></i></span><span class="val">8.8</span></div>
        <div class="row"><span>Traction</span><span class="bar"><i style="--w:72%"></i></span><span class="val">7.2</span></div>
        <div class="row"><span>Team</span><span class="bar"><i style="--w:91%"></i></span><span class="val">9.1</span></div>
        <div class="row"><span>Product demo</span><span class="bar"><i style="--w:84%"></i></span><span class="val">8.4</span></div>
        <div class="row"><span>Ambition</span><span class="bar"><i style="--w:95%"></i></span><span class="val">9.5</span></div>
        <div class="total"><span class="tag">● live</span><span>total <b>43.0</b> / 50</span></div>
      </div>
    </div>
  </div>
</section>

<section id="numbers">
  <div class="wrap">
    <div class="stats rv">
      <div class="stat"><span class="v num" data-count="5">0</span><span class="k">startups selected per cohort</span></div>
      <div class="stat"><span class="v num" data-count="8">0</span><span class="k">weeks of mentor-led program</span></div>
      <div class="stat"><span class="v num" data-count="2">0</span><span class="k">mentors matched to every team</span></div>
      <div class="stat"><span class="v num" data-count="6" data-suffix="×">0</span><span class="k">application windows per year</span></div>
    </div>
    <div style="height:28px"></div>
    <div class="sched-wrap rv">
      <table class="sched">
        <thead><tr><th>Cohort</th><th>Applications</th><th>Program</th><th>Demo Day</th><th>Status</th></tr></thead>
        <tbody>
          <tr class="open"><td>01</td><td>Oct 01 – Oct 31, 2026</td><td>Nov 16, 2026 – Jan 10, 2027</td><td>Jan 15, 2027</td><td><span class="pill live">open</span></td></tr>
          <tr><td>02</td><td>Jan 04 – Jan 31, 2027</td><td>Feb 15 – Apr 11, 2027</td><td>Apr 16, 2027</td><td><span class="pill">upcoming</span></td></tr>
          <tr><td>03</td><td>Apr 05 – Apr 30, 2027</td><td>May 17 – Jul 11, 2027</td><td>Jul 16, 2027</td><td><span class="pill">upcoming</span></td></tr>
          <tr><td>04</td><td>Jul 05 – Jul 31, 2027</td><td>Aug 16 – Oct 10, 2027</td><td>Oct 15, 2027</td><td><span class="pill">upcoming</span></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section id="faq">
  <div class="wrap">
    <div class="section-head">
      <span class="label rv">FAQ</span>
      <h2 class="rv rv-d1">Questions we get a lot.</h2>
    </div>
    <div class="faq rv">
      <details><summary>Who can apply?</summary><div class="a">Anyone currently enrolled in high school (or the equivalent), anywhere in the world, who has already started a company, product, or project with real users or revenue. Teams are welcome; at least one founder must be a high-school student. If you're under 18, a parent or guardian signs a consent form after you're selected.</div></details>
      <details><summary>What counts as "already started"?</summary><div class="a">A live product, an app in the store, a prototype people are using, a first paying customer, a newsletter with subscribers, a Discord with an active community. A pitch deck and a domain name don't count yet — but apply to the next cohort once they do.</div></details>
      <details><summary>Does it cost anything?</summary><div class="a">Nothing for founders, ever. We don't take equity and we don't take a cut of anything you raise. Revenue comes from investor and company subscriptions and from sponsors who fund the prize.</div></details>
      <details><summary>How is the program delivered?</summary><div class="a">Fully online, inside the Batch Zero app. Weekly mentor sessions on recorded video calls, biweekly cohort calls, a milestone tracker, and guest office hours. Expect 4–6 hours a week on top of school.</div></details>
      <details><summary>How do mentors and investors interact with students?</summary><div class="a">Through the platform only. Mentors are interviewed and background-checked, sessions happen on the platform, and investors and companies get visibility and intro requests — never direct contact details. Founders opt in per person, not per team.</div></details>
      <details><summary>What's the prize?</summary><div class="a">A sponsor-funded cash prize for the Demo Day winner, announced with each cohort. Every selected team also gets alumni status, the Demo Day recording, and written judge feedback.</div></details>
    </div>
  </div>
</section>

<section id="cta">
  <div class="wrap">
    <div class="cta-band rv">
      <img class="big-mark" src="/assets/img/b0-mark-paper.svg" alt="" aria-hidden="true">
      <span class="label">Cohort 01</span>
      <h2>You already built the thing. Now build the company.</h2>
      <p class="lede" style="text-align:center">Applications for Cohort 01 close October 31. Five spots.</p>
      <div class="hero-actions" style="justify-content:center">
        <a class="btn btn-primary btn-lg btn-bracket" href="/apply/founders/">I'm a founder — apply <span class="arr">→</span></a>
        <a class="btn btn-ghost btn-lg" href="/partners/">I'm a business partner</a>
      </div>
    </div>
  </div>
</section>
"""

PROGRAM = """
<div class="wrap page-hero">
  <span class="label rv">The program</span>
  <h1 class="rv rv-d1">Eight weeks. Two mentors. One Demo Day.</h1>
  <p class="lede rv rv-d2">Batch Zero is structured like a real accelerator, scaled to fit around school. Here's exactly what happens from the day you're selected to the day you pitch.</p>
</div>

<section id="timeline" style="padding-top:24px">
  <div class="wrap">
    <div class="section-head"><span class="label rv">Week by week</span><h2 class="rv rv-d1">The timeline</h2></div>
    <div class="timeline rv">
      <div class="tl-week"><span class="w">WK 01</span><span class="h">Onboarding</span><span class="d">Goal-setting, cohort kickoff, mentor matching (one domain expert, one generalist).</span></div>
      <div class="tl-week"><span class="w">WK 02</span><span class="h">Customer truth</span><span class="d">Talk to users. Re-write the problem statement with evidence, not opinion.</span></div>
      <div class="tl-week"><span class="w">WK 03</span><span class="h">Product focus</span><span class="d">Cut scope. Pick the one metric that matters for the next six weeks.</span></div>
      <div class="tl-week"><span class="w">WK 04</span><span class="h">Distribution</span><span class="d">How people find you. First growth experiments with a mentor watching.</span></div>
      <div class="tl-week"><span class="w">WK 05</span><span class="h">Money</span><span class="d">Pricing, unit economics, what "traction" means for your kind of company.</span></div>
      <div class="tl-week"><span class="w">WK 06</span><span class="h">Mid-cohort review</span><span class="d">Present progress to the other four teams and the mentor pool. Honest feedback.</span></div>
      <div class="tl-week"><span class="w">WK 07</span><span class="h">Story</span><span class="d">Deck, narrative, demo. Rehearsals with judges from previous cohorts.</span></div>
      <div class="tl-week hot"><span class="w">WK 08</span><span class="h">Demo Day</span><span class="d">Live online pitch, in-app judging, results, prize, investor and company intros.</span></div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head"><span class="label rv">What you get</span><h2 class="rv rv-d1">Inside the batch</h2></div>
    <div class="grid cols-3">
      <div class="card rv"><div class="idx"><span>//</span><span>mentors</span></div><h3>Two mentors, matched</h3><p>One who knows your domain, one who has built a company. Weekly sessions on the platform, plus async access in between.</p></div>
      <div class="card rv rv-d1"><div class="idx"><span>//</span><span>cohort</span></div><h3>Four other teams</h3><p>Biweekly cohort calls. The other founders are the part everyone says they didn't expect to matter most.</p></div>
      <div class="card rv rv-d2"><div class="idx"><span>//</span><span>tracker</span></div><h3>Milestones in-app</h3><p>Weekly goals, check-ins and a visible progress log. Mentors and judges see the same tracker you do.</p></div>
      <div class="card rv"><div class="idx"><span>//</span><span>office hours</span></div><h3>Guest experts</h3><p>Lawyers, designers, growth people, and alumni founders on a rotating schedule. Ask anything.</p></div>
      <div class="card rv rv-d1"><div class="idx"><span>//</span><span>demo day</span></div><h3>A real audience</h3><p>Investors on the subscription tier and companies on the hiring tier attend live. Intros are requested through the app afterward.</p></div>
      <div class="card rv rv-d2"><div class="idx"><span>//</span><span>alumni</span></div><h3>Alumni status</h3><p>A permanent profile, the recording, written judge feedback, and first access to every future Demo Day.</p></div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head"><span class="label rv">Selection</span><h2 class="rv rv-d1">How applications are scored</h2><p class="lede rv rv-d2">Same rubric for every team, published up front. Reviewers score independently; the top five averages get in.</p></div>
    <div class="scorecard rv" style="max-width:640px">
      <div class="hd"><span>application_rubric / v1</span><span>max 50</span></div>
      <div class="row"><span>Problem &amp; insight</span><span class="bar"><i style="--w:100%"></i></span><span class="val">/ 10</span></div>
      <div class="row"><span>Traction (users, revenue, usage)</span><span class="bar"><i style="--w:100%"></i></span><span class="val">/ 10</span></div>
      <div class="row"><span>Team</span><span class="bar"><i style="--w:100%"></i></span><span class="val">/ 10</span></div>
      <div class="row"><span>Coachability</span><span class="bar"><i style="--w:100%"></i></span><span class="val">/ 10</span></div>
      <div class="row"><span>Ambition</span><span class="bar"><i style="--w:100%"></i></span><span class="val">/ 10</span></div>
      <div class="total"><span class="tag">● published</span><span>selected <b>top 5</b> / cohort</span></div>
    </div>
  </div>
</section>

<section id="cta">
  <div class="wrap">
    <div class="cta-band rv">
      <img class="big-mark" src="/assets/img/b0-mark-paper.svg" alt="" aria-hidden="true">
      <span class="label">Cohort 01</span>
      <h2>Five spots. Applications close October 31.</h2>
      <div class="hero-actions" style="justify-content:center"><a class="btn btn-primary btn-bracket" href="/apply/founders/">Apply as a founder <span class="arr">→</span></a></div>
    </div>
  </div>
</section>
"""

ABOUT = """
<div class="wrap page-hero">
  <span class="label rv">About</span>
  <h1 class="rv rv-d1">Built by a high-school founder, for high-school founders.</h1>
</div>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="prose rv">
      <p>Batch Zero started with a simple observation: some of the most interesting startups right now are being built by people who can't legally sign the paperwork yet. They have users, sometimes revenue, and nowhere to go. College accelerators won't take them. Youth entrepreneurship programs mostly hand out trophies for ideas. Nobody was doing the thing that actually works — putting founders in a small batch, giving them mentors who've done it, and putting them in front of people who can fund and hire them.</p>
      <p>So we're building it. Batch Zero is an online accelerator that runs in cohorts of five. Every team gets two mentors, an eight-week program, and a live Demo Day judged inside the app. Investors subscribe to see the cohorts first. Companies subscribe to meet the builders early. Founders never pay.</p>
      <h2>What we believe</h2>
      <ul>
        <li><strong>Shipping is the filter.</strong> We don't select on ideas. We select on what already exists.</li>
        <li><strong>Small batches, real signal.</strong> Five teams per cohort means selection actually means something.</li>
        <li><strong>Founders don't pay.</strong> No fees, no equity, no cut of what you raise. Ever.</li>
        <li><strong>Safety by design.</strong> Adults meet students on the platform, sessions are recorded, mentors are vetted, and contact is opt-in.</li>
      </ul>
      <h2>Who's behind it</h2>
      <div class="founder">
        <div class="founder-photo">
          <picture>
            <source srcset="/assets/img/founder.webp" type="image/webp">
            <img src="/assets/img/founder.jpg" alt="Rayan Sohrabian, founder of Batch Zero" width="900" height="900" loading="lazy">
          </picture>
          <span class="hud-corner tl"></span><span class="hud-corner tr"></span><span class="hud-corner bl"></span><span class="hud-corner br"></span>
        </div>
        <div class="founder-bio">
          <span class="label">Founder</span>
          <h3>Rayan Sohrabian</h3>
          <p>Rayan started Batch Zero while still in high school in California, after getting tired of the gap between "youth entrepreneurship" and actual entrepreneurship. He builds the product, runs the cohorts, and reads every application himself.</p>
          <p>The mentor network is made up of operators and founders who volunteer two months at a time. Sponsors fund the Demo Day prize. If you want to be part of any of that, the doors are below.</p>
          <div class="founder-links"><a href="mailto:rayan@batchzero.co">rayan@batchzero.co</a></div>
        </div>
      </div>
      <div class="hero-actions" style="margin-top:12px">
        <a class="btn btn-primary btn-bracket" href="/apply/founders/">Apply as a founder</a>
        <a class="btn btn-ghost" href="/apply/mentors/">Mentor a cohort</a>
        <a class="btn btn-ghost" href="mailto:hello@batchzero.co">Sponsor a prize</a>
      </div>
    </div>
  </div>
</section>
"""

PARTNERS = """
<div class="wrap page-hero">
  <span class="label rv">Business partners</span>
  <h1 class="rv rv-d1">Which one are you?</h1>
  <p class="lede rv rv-d2">Founders never pay for Batch Zero. The people who get value from meeting them early make it possible. Pick your door — each one is a two-minute form.</p>
</div>
<section style="padding-top:16px">
  <div class="wrap">
    <div class="choose">
      <a class="choice rv" href="/apply/investors/">
        <span class="n">01</span>
        <span class="who">Investor</span>
        <h3>I want to see the cohort first.</h3>
        <p>Angels, scouts, micro-VCs, family offices. A curated feed of every selected startup, live Demo Day access, intro requests through the platform. Founding tier is free through Cohort 02.</p>
        <span class="go">Request investor access <span class="arr">→</span></span>
      </a>
      <a class="choice rv rv-d1" href="/apply/sponsors/">
        <span class="n">02</span>
        <span class="who">Sponsor company</span>
        <h3>I want to back a cohort.</h3>
        <p>Fund the Demo Day prize, put your name on a cohort, and meet the builders early — opt-in access to founders and team members for internships and project work.</p>
        <span class="go">Sponsor a cohort <span class="arr">→</span></span>
      </a>
      <a class="choice rv rv-d2" href="/apply/mentors/">
        <span class="n">03</span>
        <span class="who">Mentor</span>
        <h3>I want to give two months.</h3>
        <p>Operators, founders, engineers, designers. Two mentors per team, weekly sessions on the platform, eight weeks. Vetted, recorded, and the most direct way to change a founder's trajectory.</p>
        <span class="go">Apply to mentor <span class="arr">→</span></span>
      </a>
    </div>
    <p class="dim" style="margin-top:28px;font-size:14px">Not sure, or something else (press, schools, partnerships)? <a href="mailto:hello@batchzero.co" style="color:var(--accent-2)">hello@batchzero.co</a></p>
  </div>
</section>
"""

def form_page(label, h1, lede, aside_title, aside_items, form_fields, submit_label, done_title, done_text):
    items = "".join(f"<li>{i}</li>" for i in aside_items)
    return f"""
<div class="wrap page-hero">
  <span class="label rv">{label}</span>
  <h1 class="rv rv-d1">{h1}</h1>
  <p class="lede rv rv-d2">{lede}</p>
</div>
<section style="padding-top:16px">
  <div class="wrap">
    <div class="form-layout">
      <aside class="form-aside rv">
        <div class="req"><span class="label plain">{aside_title}</span><ul>{items}</ul></div>
        <p class="dim" style="font-size:14px">Questions before you apply? <a href="mailto:hello@batchzero.co" style="color:var(--accent-2)">hello@batchzero.co</a></p>
      </aside>
      <div class="rv rv-d1">
        <form class="app" method="post" action="#">
          {form_fields}
          <div class="form-foot">
            <span class="note">// takes about 10 minutes · you can't save a draft yet</span>
            <button class="btn btn-primary btn-bracket" type="submit">{submit_label} <span class="arr">→</span></button>
          </div>
        </form>
        <div class="form-done"><div class="ok-mark">[ ✓ ]</div><h3>{done_title}</h3><p class="dim" style="margin-top:8px">{done_text}</p></div>
      </div>
    </div>
  </div>
</section>
"""

def field(name, label, type="text", required=True, placeholder="", hint="", as_="input", options=None):
    req = "required" if required else ""
    star = " <b>*</b>" if required else ""
    if as_ == "textarea":
        ctl = f'<textarea id="{name}" name="{name}" placeholder="{placeholder}" {req}></textarea>'
    elif as_ == "select":
        opts = "".join(f'<option value="{o}">{o}</option>' for o in options)
        ctl = f'<select id="{name}" name="{name}" {req}><option value="">Select…</option>{opts}</select>'
    else:
        ctl = f'<input id="{name}" name="{name}" type="{type}" placeholder="{placeholder}" {req}>'
    h = f'<span class="hint">{hint}</span>' if hint else ""
    return f'<div class="field"><label for="{name}">{label}{star}</label>{ctl}{h}<span class="msg">// required — please fill this in</span></div>'

def chips(name, label, options):
    c = "".join(f'<label class="chip"><input type="checkbox" name="{name}" value="{o}"><span>{o}</span></label>' for o in options)
    return f'<div class="field"><label>{label}</label><div class="chips">{c}</div></div>'

def optin(name, title, sub):
    return (f'<label class="optin"><input type="checkbox" name="{name}" value="yes">'
            f'<span class="ot"><b>{title}</b><em>{sub}</em></span></label>')

def consent(text):
    return f'<label class="check"><input type="checkbox" name="consent" value="yes"><span>{text}</span></label>'

FOUNDERS_FORM = f"""
<div class="fieldset"><span class="label plain">01 · You</span>
  <div class="f-row">{field("name","Your name",placeholder="First and last")}{field("email","Email","email",placeholder="you@school.edu")}</div>
  <div class="f-row">{field("school","School + city",placeholder="Lincoln High, Los Angeles")}{field("grad_year","Graduation year",as_="select",options=["2027","2028","2029","2030"])}</div>
</div>
<div class="fieldset"><span class="label plain">02 · Your startup</span>
  <div class="f-row">{field("company","Startup name",placeholder="What do you call it?")}{field("url","Link to it","url",placeholder="https://",hint="// website, app, demo, GitHub — anything we can click")}</div>
  {field("one_liner","What does it do, in one sentence?",placeholder="We help X do Y so they can Z",hint="// no buzzwords, max 120 characters").replace('type="text"', 'type="text" maxlength="120"')}
  {field("progress","How far along are you? Numbers, please.",as_="textarea",placeholder="Users, revenue, downloads, waitlist, customers — whatever you actually have. Two or three lines.")}
  {field("why","Why this, and why you?",as_="textarea",placeholder="What do you know about this problem that most people don't? Two or three lines.")}
</div>
<div class="fieldset"><span class="label plain">03 · Team &amp; video</span>
  {field("team","Who's on the team?",placeholder="Names + what each person does. 'Just me' is fine.")}
  {field("video","60-second video","url",placeholder="https://",hint="// unlisted YouTube or Loom. Show the product, say who you are. Phone camera is fine.")}
</div>
{consent("I'm currently a high-school student. If I'm selected and under 18, a parent or guardian will sign a consent form. I agree to the <a href='/terms/' style='color:var(--accent-2)'>terms</a> and <a href='/privacy/' style='color:var(--accent-2)'>privacy policy</a>.")}
"""

MENTORS_FORM = f"""
<div class="fieldset"><span class="label plain">01 · You</span>
  <div class="f-row">{field("first_name","First name")}{field("last_name","Last name")}</div>
  <div class="f-row">{field("email","Email","email")}{field("linkedin","LinkedIn or personal site","url",placeholder="https://")}</div>
  <div class="f-row">{field("role","Current role &amp; company",placeholder="Head of Product, Acme")}{field("location","City, country")}</div>
</div>
<div class="fieldset"><span class="label plain">02 · What you bring</span>
  {chips("expertise","Where can you actually help?",["Product","Engineering","Design","Growth / marketing","Sales","Fundraising","Finance","Legal","Hardware","Consumer","B2B / SaaS","Community"])}
  {field("story","What have you built or shipped?",as_="textarea",placeholder="Two or three things you're proud of. Founders, operators, and specialists all welcome.")}
  {field("why","Why mentor a high-school founder?",as_="textarea",placeholder="Honest answer. Nobody's grading this one.")}
</div>
<div class="fieldset"><span class="label plain">03 · Commitment</span>
  {field("hours","Time you can give per week",as_="select",options=["1 hour","2 hours","3+ hours"])}
  {chips("cohorts","Which cohorts could you join?",["Cohort 01 (Nov–Jan)","Cohort 02 (Feb–Apr)","Cohort 03 (May–Jul)","Any"])}
</div>
<div class="fieldset"><span class="label plain">04 · Anything else you're open to</span>
  <p class="dim" style="font-size:13.5px;margin-top:-4px">Both optional. Tick neither and you're still a great mentor.</p>
  <div class="optin-group">
    {optin("judge_demo_day","I'm open to judging Demo Day","Score the final pitches on a fixed rubric at the end of a cohort. About two hours, online.")}
    {optin("open_to_invest","I'm open to investing","Angel or micro-investor. First checks here are usually around $10K. Nothing is committed — we'd only introduce you to a team if the founder opts in.")}
  </div>
</div>
{consent("I understand mentors are interviewed and background-checked before being matched, that sessions happen on the platform, and that I'll follow the mentor code of conduct.")}
"""

INVESTORS_FORM = f"""
<div class="fieldset"><span class="label plain">01 · You</span>
  <div class="f-row">{field("first_name","First name")}{field("last_name","Last name")}</div>
  <div class="f-row">{field("email","Email","email")}{field("firm","Firm / fund (or 'angel')")}</div>
  <div class="f-row">{field("linkedin","LinkedIn or site","url",placeholder="https://")}{field("type","Investor type",as_="select",options=["Angel","Scout","Micro-VC","VC","Family office","Syndicate lead","Other"])}</div>
</div>
<div class="fieldset"><span class="label plain">02 · What you're looking for</span>
  {chips("sectors","Sectors",["Consumer","B2B / SaaS","AI","Edtech","Fintech","Creator tools","Hardware","Climate","Health","Anything great"])}
  {field("check","Typical check size",as_="select",options=["Under $25k","$25k–$100k","$100k–$500k","$500k+","Not investing yet — want to watch"])}
  {field("why","Why early-stage teen founders?",as_="textarea",placeholder="What do you hope to find here?",required=False)}
</div>
<div class="fieldset"><span class="label plain">03 · Access</span>
  {field("tier","Tier",as_="select",options=["Founding investor (free during Cohort 01–02)","Standard subscription (from Cohort 03)"])}
  {consent("I confirm I am an accredited investor or investing through an accredited entity, and I understand Batch Zero provides visibility and introductions only — it does not broker, facilitate, or take fees on any investment.")}
</div>
"""

SPONSORS_FORM = f"""
<div class="fieldset"><span class="label plain">01 · Company</span>
  <div class="f-row">{field("company","Company")}{field("website","Website","url",placeholder="https://")}</div>
  <div class="f-row">{field("first_name","Your name")}{field("email","Work email","email")}</div>
  <div class="f-row">{field("role","Your role")}{field("size","Company size",as_="select",options=["1–10","11–50","51–200","201–1000","1000+"])}</div>
</div>
<div class="fieldset"><span class="label plain">02 · How you want to back a cohort</span>
  {chips("interest","I'm interested in",["Sponsoring the Demo Day prize","Naming a cohort","Meeting founders for internships / projects","Hosting office hours or a workshop","Something else"])}
  {field("budget","Rough sponsorship range",as_="select",options=["$1k–$5k","$5k–$15k","$15k+","Not sure yet — let's talk"])}
  {field("pitch","Why should a high-school founder want your company in the room?",as_="textarea",placeholder="Be specific — they'll read this.")}
</div>
<div class="fieldset"><span class="label plain">03 · Access</span>
  {consent("I understand all contact with students goes through the Batch Zero platform, that students opt in individually, and that engagements for anyone under 18 must comply with applicable youth-employment law and require parental consent.")}
</div>
"""

FOUNDERS = form_page("Founders · Cohort 01", "Apply to the batch.", "Five spots. You need a startup that already exists — users, revenue, a live product, a working prototype people are using. Nine questions, one link, one 60-second video. About ten minutes.",
    "What you'll need", ["A link to something real", "Numbers, even small ones", "A 60-second video (phone is fine)", "Who's on the team", "Parent/guardian consent if selected and under 18"],
    FOUNDERS_FORM, "Submit application", "Application received.", "We review every application on the same rubric and reply within two weeks of the window closing — with feedback either way.")

MENTORS = form_page("Mentors", "Give a founder two months.", "Two mentors per team, weekly sessions on the platform, eight weeks. We're looking for people who've built things and can say what they actually think.",
    "What we ask", ["1–3 hours a week for 8 weeks", "Sessions on the platform (recorded)", "A short interview and a background check", "Honest feedback, kindly delivered"],
    MENTORS_FORM, "Apply to mentor", "Thanks — we'll be in touch.", "We interview every mentor before matching. Expect a note from us within a week.")

INVESTORS = form_page("Investors", "See the cohort before anyone else.", "A curated feed of every selected startup, live Demo Day access, and intro requests routed through the platform. Founding-investor tier is free while we run the first two cohorts.",
    "How it works", ["Visibility and intros only — no deal-making on the platform", "Founders opt in before any intro", "No fees or carry, ever", "Founding tier free through Cohort 02"],
    INVESTORS_FORM, "Request access", "Request received.", "We approve investor accounts manually. You'll hear from us within a few days.")

SPONSORS = form_page("Sponsor companies", "Back a cohort. Meet the builders early.", "Sponsors fund the Demo Day prize and put their name on a cohort. In return: a seat at Demo Day, your brand in front of the next generation of founders, and opt-in access to the people already shipping — for internships, apprenticeships and project work.",
    "How it works", ["Prize sponsorship from $1k per cohort", "Logo on the cohort page and Demo Day stream", "Opt-in intros to founders and team members", "Internships, part-time, project work — never full-time placement for minors"],
    SPONSORS_FORM, "Talk to us", "Got it.", "We'll reach out within a few days to talk through the cohort and what sponsorship looks like.")

COMPANIES_REDIRECT = """
<div class="wrap page-hero"><span class="label">Moved</span><h1>This page moved.</h1><p class="lede">Companies now come in through the sponsor door. Redirecting…</p><div class="hero-actions"><a class="btn btn-primary" href="/apply/sponsors/">Go to sponsor companies →</a></div></div>
<meta http-equiv="refresh" content="2;url=/apply/sponsors/">
"""

PRIVACY = """
<div class="wrap page-hero"><span class="label">Legal</span><h1>Privacy policy</h1><p class="lede">Plain-English version first, full version below. Last updated September 9, 2026.</p></div>
<section style="padding-top:8px"><div class="wrap"><div class="prose">
<div class="card" style="margin-bottom:8px"><div class="idx"><span>tl;dr</span><span>the short version</span></div>
<p>We collect what you type into our application forms and nothing else. We use it to run Batch Zero. We don't sell it, we don't run ad trackers, and nobody outside the team sees a student's application unless that student opts in. Email <a href="mailto:rayan@batchzero.co" style="color:var(--accent-2)">rayan@batchzero.co</a> to see, fix, or delete your data at any time.</p></div>

<h2>1. Who we are</h2>
<p>Batch Zero ("Batch Zero", "we", "us") is an early-stage program based in California that is operated by its founder and has not yet formed a company. When a legal entity is formed, it will take over responsibility for this policy and we'll update this page. Questions and requests go to <a href="mailto:rayan@batchzero.co" style="color:var(--accent-2)">rayan@batchzero.co</a>.</p>

<h2>2. What we collect</h2>
<p><strong>What you give us.</strong> When you submit a form on batchzero.co we store exactly what you enter: for founders, your name, email, school, graduation year, and what you tell us about your startup and team, plus links you share (website, demo, video). For mentors, investors and sponsor companies: name, work email, company, role, links, and your answers. We also record the page the form was sent from and a general browser type, to help debug problems.</p>
<p><strong>What we don't collect.</strong> We do not use advertising trackers, social-media pixels, or analytics cookies. We don't ask for your address, phone number, date of birth, or any government ID. We don't collect payment information on this site.</p>
<p><strong>Video links.</strong> If you share a video (for example an unlisted YouTube or Loom link), the video stays on that service under its own privacy terms; we only store the link.</p>

<h2>3. How we use it</h2>
<p>To review applications, select and run cohorts, match founders with mentors, organise Demo Day, and contact you about any of that. If you're a mentor, investor or sponsor, to vet your application and, if approved, give you access to the program. We may use anonymous, aggregated numbers (for example "we received 120 applications") publicly.</p>

<h2>4. Students and parents</h2>
<p>Batch Zero is for high-school students. You must be at least 13 to use this site or apply; we do not knowingly collect information from anyone under 13, and we delete it if we find it. If you are under 18 and selected for a cohort, a parent or guardian must sign a consent form before you take part, and they can ask us at any time to see or delete your information. Parents: email <a href="mailto:rayan@batchzero.co" style="color:var(--accent-2)">rayan@batchzero.co</a> and we'll respond within a few days.</p>

<h2>5. Who can see a student's information</h2>
<p>Only the Batch Zero team and reviewers reviewing applications. Mentors see the applications of the teams they are matched with. Investors and sponsor companies do <strong>not</strong> receive contact details or full applications: they see the profile a founder chooses to make visible, and any introduction is requested through us and accepted by the founder first. We never share a student's information with a third party for that party's own marketing.</p>

<h2>6. Services we rely on</h2>
<p>Form submissions are stored in a database hosted by Supabase (United States). The website is hosted on GitHub Pages and loads fonts from Google Fonts; these providers may see standard technical data such as your IP address when your browser requests a page. Each provider handles that data under its own privacy policy. We don't use any other third-party services on this site today, and we'll update this list if that changes.</p>

<h2>7. How long we keep it</h2>
<p>Applications that aren't selected are kept for up to 12 months so you can reapply without starting over, then deleted. Selected teams' information is kept for the length of the program and up to 3 years after, for alumni purposes, unless you ask us to delete it sooner. Mentor, investor and sponsor records are kept while the relationship is active and up to 2 years after.</p>

<h2>8. Your choices and rights</h2>
<p>You can ask us to show you what we hold, correct it, or delete it, and you can withdraw an application at any time — email us and we'll do it. California residents have additional rights under the CCPA/CPRA, including the right to know, delete, and not be discriminated against for exercising those rights; we don't sell or share personal information as those laws define it. Residents of other places have similar rights under their local law and can use the same email.</p>

<h2>9. Security</h2>
<p>The site is served over HTTPS. Form data is stored in a database where the public website key can only add records, never read them; reading requires authenticated access held by the team. No system is perfectly secure, so please don't put passwords, financial details, or anything you'd consider highly sensitive into an application.</p>

<h2>10. Changes</h2>
<p>If we change this policy in a meaningful way we'll post the new version here with a new date, and if you have an active application or are in a cohort we'll email you.</p>

<p class="dim" style="font-size:14px">This policy was drafted in good faith to be clear and protective; it has not yet been reviewed by a lawyer. If anything here is unclear, ask us and we'll explain it.</p>
</div></div></section>
"""

TERMS = """
<div class="wrap page-hero"><span class="label">Legal</span><h1>Terms of use</h1><p class="lede">The rules for using batchzero.co and applying to the program. Last updated September 9, 2026.</p></div>
<section style="padding-top:8px"><div class="wrap"><div class="prose">
<div class="card" style="margin-bottom:8px"><div class="idx"><span>tl;dr</span><span>the short version</span></div>
<p>Be honest in your application. Your startup stays 100% yours. Getting in isn't guaranteed. We're a program and a community, not investors, lawyers or a bank. Adults and students only interact through us. If you're under 18, a parent signs before you join a cohort.</p></div>

<h2>1. Who's behind this</h2>
<p>Batch Zero is an early-stage program based in California, operated by its founder; it has not yet formed a company. These terms are between you and Batch Zero. When a legal entity is formed, these terms will apply between you and that entity and we'll update this page. Contact: <a href="mailto:rayan@batchzero.co" style="color:var(--accent-2)">rayan@batchzero.co</a>.</p>

<h2>2. Using the site</h2>
<p>You may use batchzero.co to learn about the program and apply. You agree not to misuse it: no scraping, no automated submissions, no attempts to access other people's data or interfere with the site. You must be at least 13 to use the site.</p>

<h2>3. Applications</h2>
<p>Everything you submit must be true and your own. You must have the right to share any links or material you include. Submitting an application doesn't guarantee selection, feedback, or a place in any cohort, and we can close, extend, or cancel an application window at our discretion. We may contact you about your application by email.</p>
<p>Applying is free. We never charge founders, take equity, or take a percentage of anything you raise.</p>

<h2>4. Joining a cohort</h2>
<p>If you're selected, taking part is subject to a separate participation agreement that covers the program in detail. If you are under 18, a parent or guardian must sign it before you start. Participation is voluntary and you can leave at any time.</p>

<h2>5. Your startup is yours</h2>
<p>You keep all rights to your company, product, code, brand, and ideas. We don't take any ownership or licence over them. With your permission, we may use your startup's name, logo and a short description to promote the program (for example on a cohort page or a Demo Day announcement); you can withdraw that permission by emailing us. Demo Day may be recorded; we'll tell you beforehand and ask for consent (from a parent or guardian if you're under 18) before publishing any recording that shows you.</p>

<h2>6. Mentors, investors and sponsors</h2>
<p>Adults take part in Batch Zero only through the platform and under our code of conduct. Mentors are interviewed and background-checked before being matched. Investors and sponsor companies receive visibility and introductions only; contact with a founder happens only after the founder (and, if under 18, their parent or guardian) opts in. Any offer of investment, internship or work is strictly between you and the other party — Batch Zero is not a party to it, does not broker or facilitate investments, and does not take fees on them.</p>

<h2>7. Not advice</h2>
<p>Batch Zero is an educational program and a community. Nothing on this site or in the program is legal, financial, tax, or investment advice. Make your own decisions and talk to a qualified adult or professional before signing anything or taking money.</p>

<h2>8. Community standards</h2>
<p>Everyone in Batch Zero — founders, mentors, investors, sponsors, staff — agrees to treat others with respect, to keep confidential what other teams share inside the program, and to follow the code of conduct we provide. We can remove anyone who breaks these rules, without notice, at our discretion.</p>

<h2>9. Our content</h2>
<p>The Batch Zero name, logo, site design and program materials belong to us. You may share links to the site freely; please don't copy or reuse our materials commercially without asking.</p>

<h2>10. No warranties, limited liability</h2>
<p>The site and program are provided "as is". We work hard to do this well but can't promise the site will always be available or error-free, or that the program will produce any particular result for your startup. To the extent the law allows, Batch Zero and the people who run it are not liable for indirect or consequential losses arising from your use of the site or participation in the program. Nothing here limits liability that cannot be limited by law.</p>

<h2>11. Changes and law</h2>
<p>We may update these terms; the date at the top tells you when. Continuing to use the site after a change means you accept it. These terms are governed by the laws of the State of California, and any dispute will be handled in the courts located there, unless the law where you live gives you protections that can't be waived.</p>

<p class="dim" style="font-size:14px">These terms were drafted in good faith to be fair and readable; they have not yet been reviewed by a lawyer. Questions: <a href="mailto:rayan@batchzero.co" style="color:var(--accent-2)">rayan@batchzero.co</a>.</p>
</div></div></section>
"""

D = "Batch Zero is an online accelerator for high-school founders: five startups per cohort, two mentors each, eight weeks, and a live Demo Day in front of investors. Free for founders."
NOTFOUND = """
<div class="wrap page-hero" style="min-height:70vh;align-content:center;text-align:center;justify-items:center">
  <span class="label">404</span>
  <h1>Nothing here yet.</h1>
  <p class="lede" style="text-align:center">That page doesn't exist — or it's part of the app we haven't shipped.</p>
  <div class="hero-actions" style="justify-content:center"><a class="btn btn-primary btn-bracket" href="/">Back to home</a><a class="btn btn-ghost" href="/apply/founders/">Apply as a founder</a></div>
</div>
"""

PAGES = [
    ("404.html", "Not found — Batch Zero", "Page not found.", NOTFOUND, "/404.html"),
    ("index.html", "Batch Zero — The accelerator for high-school founders", D, HOME, "/"),
    ("program/index.html", "The program — Batch Zero", "Eight weeks, two mentors per team, a published selection rubric and a live Demo Day. Here's the week-by-week.", PROGRAM, "/program/"),
    ("about/index.html", "About — Batch Zero", "Built by a high-school founder, for high-school founders. Why Batch Zero exists and what we believe.", ABOUT, "/about/"),
    ("apply/founders/index.html", "Apply as a founder — Batch Zero", "Apply to Cohort 01. Five spots for high-school startups that already exist.", FOUNDERS, "/apply/founders/"),
    ("apply/mentors/index.html", "Become a mentor — Batch Zero", "Give a high-school founder two months. Weekly sessions, vetted mentors, real impact.", MENTORS, "/apply/mentors/"),
    ("apply/investors/index.html", "Investor access — Batch Zero", "See every selected startup first. Demo Day access and intro requests through the platform.", INVESTORS, "/apply/investors/"),
    ("partners/index.html", "Business partners — Batch Zero", "Investors, sponsor companies and mentors: pick your door into Batch Zero.", PARTNERS, "/partners/"),
    ("apply/sponsors/index.html", "Sponsor a cohort — Batch Zero", "Fund the Demo Day prize, name a cohort, and meet high-school founders early.", SPONSORS, "/apply/sponsors/"),
    ("apply/companies/index.html", "Moved — Batch Zero", "This page moved to sponsor companies.", COMPANIES_REDIRECT, "/apply/sponsors/"),
    ("privacy/index.html", "Privacy policy — Batch Zero", "What Batch Zero collects, why, who can see it, and how students and parents can ask for it to be deleted.", PRIVACY, "/privacy/"),
    ("terms/index.html", "Terms of use — Batch Zero", "The rules for using batchzero.co and applying to the program.", TERMS, "/terms/"),
]
