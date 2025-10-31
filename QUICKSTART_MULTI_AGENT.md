# Quick Start Guide - Multi-Agent System

Get started with the multi-agent financial analysis system in 5 minutes!

## 🚀 Installation

```bash
# 1. Install dependencies (if not already done)
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## ⚡ Quick Test

### Test 1: Simple Chat Query
```bash
python -m agent.app_multi_agent "[Chat] What's Apple's P/E ratio?"
```

**Expected output**: A 3-4 paragraph response with Apple's P/E ratio and context.

**Time**: ~10 seconds

### Test 2: Report Query
```bash
python -m agent.app_multi_agent "[Report] Analyze Microsoft"
```

**Expected output**: A comprehensive 8-15 section report on Microsoft.

**Time**: ~60 seconds

## 📝 Basic Usage Patterns

### Pattern 1: Simple Metric Lookup
```bash
# Get a specific metric
python -m agent.app_multi_agent "[Chat] What's Tesla's profit margin?"

# Compare companies
python -m agent.app_multi_agent "[Chat] Compare Apple and Google"
```

### Pattern 2: Current Events
```bash
# Market news
python -m agent.app_multi_agent "[Chat] What happened in the market today?"

# Company news
python -m agent.app_multi_agent "[Chat] Latest news on NVIDIA"
```

### Pattern 3: Comprehensive Analysis
```bash
# Full company analysis
python -m agent.app_multi_agent "[Report] Analyze Tesla's financial health"

# Industry deep dive
python -m agent.app_multi_agent "[Report] Deep dive into semiconductor industry"
```

## 🎮 Interactive Mode

```bash
# Start interactive session
python -m agent.app_multi_agent

# Then enter queries:
You: [Chat] What's NVDA's current price?
You: [Report] Analyze Amazon
You: quit  # to exit
```

## 🎯 Understanding Tags

### [Chat] Tag
- Quick responses (3-4 paragraphs)
- Uses 1-3 tools
- Conversational tone
- ~10 seconds

**Examples**:
```
[Chat] What's Apple's P/E ratio?
[Chat] Compare Microsoft and Google
[Chat] What happened to Tesla today?
```

### [Report] Tag
- Comprehensive reports (8-15 sections)
- Uses 5-10+ tools
- Professional tone
- ~60 seconds

**Examples**:
```
[Report] Analyze Tesla's financial health
[Report] Compare Apple vs Microsoft
[Report] Deep dive into Meta's strategy
```

### Length Customization
```
[Chat] Give me 2 sentences on Tesla
[Chat] 5 paragraphs on Amazon's growth
Compare AAPL and MSFT [Chat] keep it brief
```

## 📊 Example Outputs

### Chat Output Example
```markdown
Apple (AAPL) currently has a P/E ratio of 28.5, which is slightly above
the tech sector average of 25.3. This suggests the market has confidence
in Apple's future earnings potential.

The company's valuation is supported by strong profitability metrics, with
a profit margin of 25.4% and ROE of 147%. Recent news indicates solid
iPhone sales and growing services revenue.

*Note: This is informational analysis, not investment advice.*
```

### Report Output Example
```markdown
# Apple Inc. Financial Analysis Report

## Executive Summary

Apple demonstrates strong financial health with premium valuation...

## 1. Market Performance

| Metric | Value |
|--------|-------|
| Current Price | $178.45 |
| 52-Week High | $199.62 |
| 52-Week Low | $164.08 |

[... continues for 8-15 sections ...]
```

## 🔧 Troubleshooting

### Issue: "No module named agent"
```bash
# Run from the Finassistant directory:
cd /Users/nishant/Desktop/Finassistant
python -m agent.app_multi_agent "[Chat] test"
```

### Issue: "API key not found"
```bash
# Make sure .env file exists and has:
GOOGLE_API_KEY=your_actual_api_key_here
```

### Issue: Slow responses
- **Chat mode** should be ~10 seconds
- **Report mode** can take 60-90 seconds (this is normal)
- Check your internet connection for web search tools

## 📚 Next Steps

1. **Try the examples**:
   ```bash
   python examples/multi_agent_examples.py demo
   ```

2. **Read full documentation**:
   - See [MULTI_AGENT_README.md](MULTI_AGENT_README.md)

3. **Explore available tools**:
   - See [MULTI_AGENT_README.md#-available-tools-23-total](MULTI_AGENT_README.md#-available-tools-23-total)

4. **Run in interactive mode**:
   ```bash
   python -m agent.app_multi_agent
   ```

## 🎓 Learning Path

### Beginner
1. Start with simple [Chat] queries
2. Try different companies (AAPL, MSFT, GOOGL, TSLA, AMZN, NVDA)
3. Experiment with comparisons

### Intermediate
1. Use length customization
2. Try [Report] mode for deeper analysis
3. Combine multiple aspects (valuation + news)

### Advanced
1. Compare 3+ companies
2. Request specific tool combinations
3. Use for research workflows

## 💡 Pro Tips

1. **Be specific**: "What's Apple's P/E ratio?" is better than "Tell me about Apple"

2. **Use tickers**: AAPL, MSFT, GOOGL (uppercase works best)

3. **Choose the right mode**:
   - Need quick answer? Use [Chat]
   - Need full analysis? Use [Report]

4. **Customize length**: Add "brief", "detailed", or specific paragraph counts

5. **Chain queries**: Use interactive mode for follow-up questions

## 🚨 Common Mistakes

❌ **Don't**: `Analyze Apple` (missing tag)
✅ **Do**: `[Chat] Analyze Apple` or `[Report] Analyze Apple`

❌ **Don't**: `What's aapl pe?` (unclear)
✅ **Do**: `[Chat] What's Apple's P/E ratio?`

❌ **Don't**: Expect instant results in Report mode
✅ **Do**: Wait 60-90 seconds for comprehensive reports

## 🎉 Success Checklist

- [ ] Ran a simple [Chat] query
- [ ] Ran a [Report] query
- [ ] Tried company comparison
- [ ] Used custom length specification
- [ ] Explored interactive mode
- [ ] Read the full documentation

---

**Questions?** Check [MULTI_AGENT_README.md](MULTI_AGENT_README.md) for detailed documentation.

**Issues?** The system includes detailed error messages and graceful fallbacks.
