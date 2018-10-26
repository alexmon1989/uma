const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const VueLoaderPlugin = require('vue-loader/lib/plugin');

module.exports = {
    mode: 'development',
    context: __dirname,
    entry: './assets/js/index',
    output: {
        path: path.resolve('./assets/bundles/'),
        filename: 'app.js'
    },

    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new VueLoaderPlugin(),
        new webpack.ProvidePlugin({
            jQuery: 'jquery',
            '$': 'jquery',
            'window.jQuery': 'jquery',
        }),
    ],

    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader'
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            },
            {
                test: /\.scss$/,
                use: [
                    {
                        loader: "style-loader" // creates style nodes from JS strings
                    },
                    {
                        loader: "css-loader" // translates CSS into CommonJS
                    },
                    {
                        loader: "sass-loader" // compiles Sass to CSS
                    }
                ]
            },
            {
                test: /\.(png|woff|woff2|eot|ttf|svg)$/,
                loader: 'file-loader',
                options: {
                    publicPath: '/static/bundles/'
                }
            }
        ],
    },
    resolve: {
        modules: ['node_modules'],
        alias: {vue: 'vue/dist/vue.js'}
    },

};
