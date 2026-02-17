# AI Factory - Operations Guide

## Daily Workflow

### Morning (5 min)
```bash
python cli.py daily_run
```

This checks:
- Sales from yesterday
- Top performing tools
- Content performance
- What to build next

### Key Metrics to Watch

1. **Revenue per tool** - Identify winners
2. **Click-through rate** - Are people visiting?
3. **Conversion rate** - Are they buying?

## Troubleshooting

### "Product not found" when publishing
- Check `LEMONSQUEEZY_API_KEY` in .env
- Verify store ID is correct

### Content not posting
- Verify API credentials in .env
- Check rate limits
- For YouTube: re-authenticate OAuth

### Database locked
- Close any other connections
- Check file permissions

## Scaling Strategy

### Phase 1: First Sales (Week 1-2)
- Build 3 tools from templates
- Post 1 piece of content/day
- Goal: 5-10 sales/day

### Phase 2: Traffic Growth (Week 3-4)
- Double posting frequency
- A/B test captions
- Goal: $500-1500/day

### Phase 3: Scaling (Month 2+)
- Identify winner clone it
- Bundle products
- Increase ad spend (optional)
- Goal: $5K-15K/week

## Safety Rules

1. **Never scrape** - Use official APIs only
2. **No spam** - Space out content
3. **Own accounts** - Your Stripe, your Gumroad, etc.
4. **Monitor** - Check daily for issues

## Manual Overrides

### Close a position manually
```bash
# Edit db/factory.db directly with sqlite3
sqlite3 db/factory.db
```

### Force post content
```bash
python cli.py post_content --platform youtube
```

### Reset database
```bash
rm db/factory.db
python cli.py init
```
