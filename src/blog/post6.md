### Static Website Rebuild
Goals - completely static, save on hosting charges + remove as much JS as possible

### Build Process (build.py)
React has alot of pros in terms of reusability - I didn't want to lose that
I could use Jinja, but Markdown is not natively supported, and I kind of just wanted to do it myself

The several optimizations
 - snippets
 - cache busting
 - recursive snippet insertion
 - python in HTML


### Speed Comparison
Initial page load much better; still a lot I could do on the audit front, but it is faster
we have to tradeoff with the slower loads in between, but the static routing is nice

