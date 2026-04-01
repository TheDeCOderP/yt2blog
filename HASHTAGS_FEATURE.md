# Hashtags Feature

The app now automatically generates relevant hashtags for each blog post using Gemini AI.

## What's New

### Hashtag Generation
- **Automatic**: Hashtags are generated automatically when you create a blog post
- **Smart**: Uses the blog title and content to generate 10-15 relevant hashtags
- **Saved**: Hashtags are stored in the metadata and persist in history

### Display Locations

1. **After Blog Generation** (Generate Page)
   - Shows suggested hashtags in a styled section
   - Click any hashtag to copy it to clipboard
   - Hashtags are clickable for easy copying

2. **In History View** (History Page)
   - When viewing a saved blog, hashtags are displayed below stats
   - Same click-to-copy functionality

### How It Works

1. Blog is generated with Gemini 2.5 Flash
2. Hashtags are generated based on:
   - Blog title
   - Blog content (first 1000 characters)
   - Content relevance and trending topics
3. Hashtags are saved to `meta_*.json` files
4. Hashtags are displayed with copy-to-clipboard functionality

### Technical Details

- **Function**: `generate_hashtags(blog_content, blog_title, llm)`
- **Storage**: Saved in metadata JSON alongside language and tone
- **Limit**: Maximum 15 hashtags per blog
- **Format**: Each hashtag starts with `#`
- **UI**: Styled chips with hover effects and click-to-copy

### Example Output

```
#ContentMarketing #BlogWriting #AIGenerated #SEO #DigitalStrategy
#ContentCreation #MarketingTips #SocialMedia #Engagement #Growth
#OnlineMarketing #WebContent #PublishingTips #CreativeWriting #Trending
```

### Usage

No additional configuration needed! Hashtags are generated automatically for every new blog post.

To use hashtags:
1. Generate a blog post normally
2. Scroll down to see "🏷️ Suggested Hashtags"
3. Click any hashtag to copy it
4. Paste on social media (Twitter, LinkedIn, Instagram, etc.)

### Customization

To modify hashtag generation:
- Edit the `generate_hashtags()` function in `app.py`
- Adjust the prompt to change hashtag style or count
- Modify the regex pattern to filter hashtags differently

### Troubleshooting

If hashtags aren't generating:
1. Check that Gemini API key is valid
2. Ensure blog content is substantial (>100 words)
3. Check PM2 logs: `pm2 logs yt2blog-3030`
4. Hashtags are optional - blog generation continues even if hashtag generation fails
