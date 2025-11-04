# 🚀 Vercel Deployment Guide - Frontend

## **Prerequisites**
- GitHub account with the repository pushed
- Vercel account (sign up at https://vercel.com)

---

## **Step-by-Step Deployment**

### **1. Import Project to Vercel**

1. Go to https://vercel.com/dashboard
2. Click **"Add New Project"**
3. Select **"Import Git Repository"**
4. Choose **`titanite07/autonomous-research-agent`**
5. Click **"Import"**

---

### **2. Configure Build Settings**

Vercel will auto-detect Next.js, but verify these settings:

#### **Project Settings:**
```
Project Name: autonomous-research-agent-frontend
Framework Preset: Next.js
```

#### **Root Directory:**
```
frontend
```
⚠️ **IMPORTANT**: Click "Edit" next to Root Directory and set it to `frontend`

#### **Build and Output Settings:**

```yaml
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Development Command: npm run dev
```

**Screenshot Reference:**
```
┌─────────────────────────────────────────┐
│ Root Directory:           frontend      │  ← Set this!
│ Build Command:            npm run build │
│ Output Directory:         .next         │
│ Install Command:          npm install   │
│ Development Command:      npm run dev   │
└─────────────────────────────────────────┘
```

---

### **3. Environment Variables**

Click **"Environment Variables"** and add:

#### **Production Environment Variables:**

| Variable Name | Value | Notes |
|---------------|-------|-------|
| `NEXT_PUBLIC_API_URL` | `https://autonomous-research-agent-backend.onrender.com` | Your Render backend URL |
| `NODE_VERSION` | `20.11.0` | Node.js version |

**How to Add:**
```
1. Variable Name:  NEXT_PUBLIC_API_URL
   Value:          https://autonomous-research-agent-backend.onrender.com
   Environments:   ☑ Production  ☑ Preview  ☑ Development

2. Variable Name:  NODE_VERSION
   Value:          20.11.0
   Environments:   ☑ Production  ☑ Preview  ☑ Development
```

⚠️ **CRITICAL**: Make sure `NEXT_PUBLIC_API_URL` starts with `NEXT_PUBLIC_` (Next.js requirement for browser-accessible env vars)

---

### **4. Deploy!**

1. Click **"Deploy"**
2. Wait 2-3 minutes for build
3. Vercel will provide your URL: `https://autonomous-research-agent-frontend.vercel.app`

---

## **Vercel Dashboard - Quick Reference**

### **Settings to Fill:**

```yaml
# General Settings
Project Name: autonomous-research-agent-frontend
Framework: Next.js

# Build & Development Settings
Root Directory: frontend                    # ← CRITICAL!
Build Command: npm run build
Output Directory: .next
Install Command: npm install

# Environment Variables
NEXT_PUBLIC_API_URL: https://autonomous-research-agent-backend.onrender.com
NODE_VERSION: 20.11.0
```

---

## **Expected Build Output**

You should see:
```
✓ Detected Next.js
✓ Installing dependencies...
✓ Building application...
✓ Optimizing pages...
✓ Generating static pages...
✓ Build completed successfully
✓ Deployment ready

Live URL: https://autonomous-research-agent-frontend.vercel.app
```

---

## **Post-Deployment Checklist**

### ✅ **Verify Frontend:**
1. Visit your Vercel URL
2. Check if the UI loads
3. Try searching for "BERT"
4. Verify no CORS errors in browser console (F12)

### ✅ **Update Backend CORS (if needed):**

If you get CORS errors, add Vercel domain to backend:

1. **Edit `api/main.py`:**
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://*.vercel.app",                                    # Already there
    "https://autonomous-research-agent-frontend.vercel.app",   # Add specific URL
    "https://*.onrender.com",
]
```

2. **Commit and push:**
```bash
git add api/main.py
git commit -m "Add Vercel URL to CORS"
git push origin main
```

3. Wait for Render to redeploy backend (~5 min)

---

## **Troubleshooting**

### ❌ **Build Failed: "Module not found"**
**Solution:** Make sure Root Directory is set to `frontend`

### ❌ **Runtime Error: "API_BASE_URL is undefined"**
**Solution:** Check that `NEXT_PUBLIC_API_URL` is set in Environment Variables

### ❌ **CORS Error in Browser**
**Solution:** Add your Vercel URL to backend CORS configuration (see above)

### ❌ **404 on API Calls**
**Solution:** Verify `NEXT_PUBLIC_API_URL` doesn't have trailing slash:
```
✅ Correct: https://autonomous-research-agent-backend.onrender.com
❌ Wrong:   https://autonomous-research-agent-backend.onrender.com/
```

---

## **Architecture After Deployment**

```
┌─────────────────────────────────────────────────────────┐
│                      USER BROWSER                        │
│                  (Your customers)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              VERCEL (Frontend)                           │
│  https://autonomous-research-agent-frontend.vercel.app   │
│                                                          │
│  - Next.js UI                                           │
│  - React Components                                     │
│  - shadcn/ui                                           │
└────────────────────┬────────────────────────────────────┘
                     │ API Calls
                     │ (NEXT_PUBLIC_API_URL)
                     ▼
┌─────────────────────────────────────────────────────────┐
│            RENDER (Backend)                              │
│  https://autonomous-research-agent-backend.onrender.com  │
│                                                          │
│  - FastAPI Server                                       │
│  - Research System                                      │
│  - Paper Scrapers (arXiv, Semantic Scholar, Springer)  │
│  - Database (SQLite)                                    │
└─────────────────────────────────────────────────────────┘
```

---

## **Cost Breakdown**

| Service | Plan | Cost | What You Get |
|---------|------|------|--------------|
| **Vercel** | Hobby | **FREE** | Unlimited bandwidth, 100 deployments/day |
| **Render** | Free | **FREE** | 750 hours/month (enough for 24/7) |
| **Groq API** | Free | **FREE** | Unlimited inference (rate limited) |
| **Total** | | **$0/month** | Production-ready deployment! |

---

## **Vercel Advantages Over Render for Frontend**

✅ **Faster Cold Starts** - Instant edge deployment  
✅ **Global CDN** - Content served from nearest location  
✅ **Automatic HTTPS** - Free SSL certificates  
✅ **Git Integration** - Auto-deploy on push  
✅ **Preview Deployments** - Every PR gets a preview URL  
✅ **Analytics** - Built-in performance monitoring  

---

## **Next Steps After Deployment**

1. ✅ Test the full search workflow
2. ✅ Share your live URL with friends/colleagues
3. ✅ Set up custom domain (optional)
4. ✅ Enable Vercel Analytics (free)
5. ✅ Add to your portfolio/resume

---

## **Custom Domain (Optional)**

If you have a domain:

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain (e.g., `research-agent.yourdomain.com`)
3. Update DNS records as instructed
4. Wait for DNS propagation (~1 hour)
5. Update `NEXT_PUBLIC_API_URL` if backend domain changed

---

## **Continuous Deployment**

Now every time you push to GitHub:
- ✅ Vercel auto-deploys frontend (2-3 min)
- ✅ Render auto-deploys backend (5-10 min)

**Workflow:**
```bash
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin main

# Automatic deployments triggered:
# → Vercel rebuilds frontend
# → Render rebuilds backend
```

---

## **Support & Resources**

- Vercel Docs: https://vercel.com/docs
- Next.js Docs: https://nextjs.org/docs
- Render Docs: https://render.com/docs
- Your GitHub Repo: https://github.com/titanite07/autonomous-research-agent

---

## **Quick Copy-Paste Values for Vercel**

**Root Directory:**
```
frontend
```

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://autonomous-research-agent-backend.onrender.com
NODE_VERSION=20.11.0
```

**Build Command:**
```
npm run build
```

**Output Directory:**
```
.next
```

---

Good luck with your deployment! 🚀
