import React from 'react'

export default function LandingPage() {
  return (
    <div className="wrap">
      <header>
        <div className="header-inner">
          <div className="brandmark" aria-hidden />
          <div style={{ display: 'grid' }}>
            <div className="title">Learning Assistant</div>
            <div className="sub">AI-Powered Q&A • RAG • FastAPI • Vite</div>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="panel" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h1 style={{ fontSize: '3rem', fontWeight: 800, marginBottom: '16px' }}>
            Your AI Learning Assistant
          </h1>
          <p style={{ fontSize: '1.1rem', color: 'var(--muted)', maxWidth: '700px', margin: '0 auto 24px' }}>
            Upload your documents and get instant, accurate answers. Learn faster with AI-powered insights
            from your own files.
          </p>
          <a
            href="/chat"
            className="btn primary"
            style={{ padding: '14px 24px', fontSize: '1rem', marginTop: '16px' }}
          >
            Try the Demo
          </a>
        </section>

        {/* Features Section */}
        <section className="panel" style={{ padding: '40px 20px', marginTop: '24px' }}>
          <h2 style={{ textAlign: 'center', fontSize: '2rem', fontWeight: 700, marginBottom: '32px' }}>
            Key Features
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '24px',
            }}
          >
            <div className="panel" style={{ padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>💬</div>
              <h3 style={{ fontWeight: 700, marginBottom: '8px' }}>Natural Conversations</h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
                Chat with AI like a human tutor.
              </p>
            </div>
            <div className="panel" style={{ padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📄</div>
              <h3 style={{ fontWeight: 700, marginBottom: '8px' }}>Document Q&A</h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
                Upload PDFs, DOCX, or TXT and get instant answers.
              </p>
            </div>
            <div className="panel" style={{ padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🧠</div>
              <h3 style={{ fontWeight: 700, marginBottom: '8px' }}>Smart Learning</h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
                AI adapts to your context and knowledge.
              </p>
            </div>
            <div className="panel" style={{ padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🌐</div>
              <h3 style={{ fontWeight: 700, marginBottom: '8px' }}>Multi-Language</h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
                Supports multiple languages for global learners.
              </p>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="panel" style={{ padding: '40px 20px', marginTop: '24px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '32px' }}>How It Works</h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '24px',
            }}
          >
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>1️⃣</div>
              <h3 style={{ fontWeight: 700 }}>Upload</h3>
              <p style={{ color: 'var(--muted)' }}>Add your documents or knowledge base.</p>
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>2️⃣</div>
              <h3 style={{ fontWeight: 700 }}>Ask</h3>
              <p style={{ color: 'var(--muted)' }}>Type your question in natural language.</p>
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>3️⃣</div>
              <h3 style={{ fontWeight: 700 }}>Learn</h3>
              <p style={{ color: 'var(--muted)' }}>Get instant, accurate answers and explanations.</p>
            </div>
          </div>
        </section>
      </main>

      <footer style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--muted)', marginTop: '24px' }}>
       Learning Assistant © {new Date().getFullYear()}
      </footer>
    </div>
  )
}
