const path = require('path');
const webpack = require('webpack');

const MiniCssExtractPlugin = require("mini-css-extract-plugin");
// const { createLodashAliases } = require('lodash-loader');
const { VueLoaderPlugin } = require('vue-loader');


module.exports = (env, argv) => Object({
    context: __dirname,
    entry: './assets/index',

    output: {
        path: path.resolve('static/aircox_web/assets'),
        filename: '[name].js',
        chunkFilename: '[name].js',
    },

    optimization: {
        usedExports: true,
        concatenateModules: argv.mode == 'production' ? true : false,

        splitChunks: {
            cacheGroups: {
                vendor: {
                    name: 'vendor',
                    chunks: 'initial',
                    enforce: true,

                    test: /[\\/]node_modules[\\/]/,
                },
            }
        }
    },

    plugins: [
        new MiniCssExtractPlugin({
            filename: "[name].css",
            chunkFilename: "[id].css"
        }),
        new VueLoaderPlugin(),
    ],

    module: {
        rules: [
            {
                test: /\/node_modules\//,
                sideEffects: false
            },
            {
                test: /\.css$/,
                use: [ { loader: MiniCssExtractPlugin.loader },
                       'css-loader' ]
            },
            {
                // TODO: remove ttf eot svg
                test: /\.(ttf|eot|svg|woff2?)$/,
                use: [{
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'fonts/',
                    }
                }],
            },
            { test: /\.vue$/, use: 'vue-loader' },
        ],
    },

    resolve: {
        alias: {
            js: path.resolve(__dirname, 'assets/js'),
            vue: path.resolve(__dirname, 'assets/vue'),
            css: path.resolve(__dirname, 'assets/css'),
            vue: 'vue/dist/vue.esm.browser.js',
            // buefy: 'buefy/dist/buefy.js',
        },
        modules: [
            'assets/css',
            'assets/js',
            'assets/vue',
            './node_modules',
        ],
        extensions: ['.js', '.vue', '.css', '.styl', '.ttf']
    },
})

