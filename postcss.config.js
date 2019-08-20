module.exports = {
  plugins: [
    require('autoprefixer'),
    require('cssnano')({
      preset: 'default',
    }),
    require('postcss-uncss')({
      html: ['build/**/*.html'],
      ignore: ['.navbar-menu-drawer.is-active',
        '.navbar-burger.is-active',
        '.navbar-burger.is-active span',
        '.navbar-burger.is-active span:first-child',
        '.navbar-burger.is-active span:nth-child(2)',
        '.navbar-burger.is-active span:nth-child(3)',
        '#sidenav-overlay.is-active']
    })
  ],
};
