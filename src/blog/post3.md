Over the past year, I have slowly rebuilt my personal website (this one!) from scratch. Doing so let me learn and use tons of different technologies throughout the entire web stack. While I was building this site, I had to do tons of [Googling](https://fossbytes.com/do-best-programmers-use-google-stack-overflow-time/)/[StackOverflowing](https://www.quora.com/How-often-do-professional-programmers-use-Stack-Overflow), because all of the tutorials and resources I wanted to use were widely spread around the web. I wanted to take this chance to do a full write-up(/compilation of tutorials) on how to start from nothing and build up a full website, leaving (almost) no details out. Enjoy!

I built the front end of this site using only two external dependencies: React and React Router (no CSS frameworks!).

## Structure
Web pages are traditionally created in [HyperText Markup Language](https://developer.mozilla.org/en-US/docs/Web/HTML), but I decided for this website that I would instead use [React](https://reactjs.org/), a self-described "JavaScript library for building user interfaces." A common complaint (or feature, according to some) about traditional web development is that the HTML (which provides the structure of the interface) and [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript) (which provides interactivity) are separated from each other; however, these two components of the front end are inherently intertwined, as they are both providing the user interface. React addresses this point by providing a JavaScript framework in which the entire user interface is written as separate components that are interactive by nature. I would recommend going through the [React Tutorial](https://reactjs.org/tutorial/tutorial.html) to get started with React - also check out [my notes](https://rahulyesantharao.com/blog/posts/mit-splash-2017) on React!

Most of the code is fairly common stateful React component management, so I won't go into it here; however, I did want to mention my animation component, which I made to manage the CSS page transitions on the site. I found that React Transition Group is fairly difficult to combine with React Router, so I instead built a [PageAnimationWrapper](https://github.com/rahulyesantharao/personal-website-m2/blob/master/src/components/common/PageAnimationWrapper.js) component to handle page transitions.

The component functions as a wrapper that holds each Route component and manages when it is visible, using CSS classes to fade the page in whenever it becomes visible. The way it does this is by keeping one state variable, `show`, which tracks whether or not the page should be shown at the moment. The key display code is

    #!javascript
    let className = (this.state.show)?"page-1":"page-0";
    return (
      <div className={"page-wrapper " + className} style={pageStyle}>
        {this.state.show && this.props.children}
      </div>
    );

which calculates the CSS class, `page-1` and `page-0`, which are visible and invisible, respectively, and loads the page if the `show` state is set. The state is set through a prop, `mounted`, which is used to set/unset `show` every time it is updated. Check out the [code](https://github.com/rahulyesantharao/personal-website-m2/blob/master/src/components/common/PageAnimationWrapper.js) for the full details.

## Styling
Web styling is done using [Cascading Style Sheets](https://developer.mozilla.org/en-US/docs/Web/CSS). However, directly writing CSS is extremely painstaking, so I opted instead to use a [CSS preprocessor](https://developer.mozilla.org/en-US/docs/Glossary/CSS_preprocessor): [SASS](https://sass-lang.com/). A CSS preprocessor is essentially a language that provides features that make writing CSS easier and compiles down to basic CSS - in particular, SASS includes for/if control statements, variables, and nested styling rules. To get started with styling websites, I recommend going through these [CSS Tutorials](https://developer.mozilla.org/en-US/docs/Learn/CSS) and then the [SASS Tutorials](https://sass-lang.com/guide).

In order to make the structure of the website more manageable, I created my own grid system, based heavily on the grid system in [Bulma](https://bulma.io/). You can check it out [here](https://github.com/rahulyesantharao/personal-website-m2/blob/master/src/sass/layout/columns.scss) - it uses the for loops in SASS to concisely declare a responsive 12-column grid system. This file demonstrates the power of SASS to significantly improve the styling experience. Besides the grid, I also created a CSS [reset file](https://cssreset.com/what-is-a-css-reset/) that combines elements from several popular resets (see [here](https://github.com/rahulyesantharao/personal-website-m2/blob/master/src/sass/base/reset.scss)). Finally, on top of that I declared several basic site styles, making extensive use of SASS's variables in order to easily declare and use a consistent color/sizing scheme throughout the site.

## Routing
The final component of Front-End web development is routing. This was traditionally a backend task, as, in the original client-server model, the client would request each URL from the server, and the server would respond with the appropriate resource based on the request. However, front end JavaScript libraries, such as React, make use of front-end routing to make the website faster for users.

The original model of sending a request to the server for every single URL incurs a high network-cost for users that often outweighs the actual size of the page they are fetching - this is especially true for small websites such as mine. Thus, front-end routing allows the client to load the entire website in the initial page load (when https://rahulyesantharao.com/ is loaded) and simply uses JavaScript to change the view based on users navigating through the page. [React Router](https://reacttraining.com/react-router/) provides a clean, React-friendly way to declare routes in React projects. After learning React, it is definitely worth checking out [a tutorial](https://medium.com/@pshrmn/a-simple-react-router-v4-tutorial-7f23ff27adf) to get started with React Router.

## (Extra) Environment Setup
It is easy enough to learn the various technologies I mentioned above individually; however, it is much harder to actually get a real React development environment set up, so I will walk through a minimal environment setup. It is worth noting that, instead of making your own setup, you can just use [Create React App](https://github.com/facebook/create-react-app), but it is fun to see all the different tools used.

The key packages are Babel, Webpack, and Express.

[Babel](https://babeljs.io/) is a JavaScript [transpiler](https://en.wikipedia.org/wiki/Source-to-source_compiler) - this is useful because, while JavaScript is currently at [ECMAScript 2017](https://www.ecma-international.org/publications/standards/Ecma-262.htm), most browsers still do not reliably support versions past ES5. You can read more about ECMAScript versioning [here](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Language_Resources). Thus, we are able to use all of the nice, new features of ES2017 during development, but still support all browsers by transpiling to ES5. The instructions for use with Webpack are found [here](https://babeljs.io/docs/setup/#installation).

[Webpack](https://webpack.js.org/) is a JavaScript bundler that bundles together all of the JS code and package dependencies for the project. It also allows us to automate significant portions of the build process. There are several steps involved to go from React code and CSS to a functioning website. These include

1. Bundling and transpiling all of the React code.
2. Bundling all of the external dependencies.
3. Bundling and transpiling all of the SASS code.
4. Postprocessing the CSS to include the proper prefixes.
5. Minifying the JS and CSS.
6. Include all of the bundled files in the HTML index file.

All of these steps can be included as part of the Webpack bundling process through various Webpack [loaders](https://webpack.js.org/loaders/) and [plugins](https://webpack.js.org/plugins/). Loaders allow you to incorporate third party tools, such as Babel and [PostCSS](http://postcss.org/) into the bundling process, in order to accomplish the transpiling and postprocessing. Plugins on the other hand are mainly extensible Webpack tools that allow you to customize the bundling process, including plugins to [split the CSS out into separate files](https://webpack.js.org/plugins/extract-text-webpack-plugin/) and [create HTML files with the bundles included](https://webpack.js.org/plugins/html-webpack-plugin/). I would recommend checking out the [Webpack Concepts](https://webpack.js.org/concepts/) in order to get started. Afterwards, check out 

 - [File Loader](https://webpack.js.org/loaders/file-loader/)
 - [Babel Loader](https://github.com/babel/babel-loader)
 - [CSS Loader](https://github.com/webpack-contrib/css-loader)
 - [PostCSS Loader](https://github.com/postcss/postcss-loader)
 - [PurifyCSS Webpack](https://github.com/webpack-contrib/purifycss-webpack)
 - [URL Loader](https://github.com/webpack-contrib/url-loader)
 - [Style Loader](https://github.com/webpack-contrib/style-loader)
 - [SASS Loader](https://github.com/webpack-contrib/sass-loader)

to get a full Webpack config.

The final portion of the development environment is the development server. While we are developing, we generally want to have a quick server to test out the website and make incremental changes. There are two main options to set up a development server. The easier of the two is [webpack-dev-server](https://webpack.js.org/configuration/dev-server/) - a configurable dev server that serves the bundle straight from the webpack build. This is a good and easy to use option that includes many features that make development fast. The second option is using [Express](https://expressjs.com/) and [webpack-dev-middleware](https://github.com/webpack/webpack-dev-middleware). These two tools are what webpack-dev-server uses behind the scenes, but you can directly use them to set up your own custom dev server, at the cost of a greater amount of initial set up time. If this sounds interesting, it is definitely cool to set up a basic server to get a feeling for how it works.

After getting familiar with all the tools I mentioned here, you might find it useful to check out my [repo for this website](https://github.com/rahulyesantharao/personal-website-m2) to get a feel for what a full environment setup might look like.

I hope you enjoyed this write-up and found it useful to get started with web development. Check back soon for Part 2: The Back End!
