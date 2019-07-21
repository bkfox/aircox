const path = require('path');
const webpack = require('webpack');

const MiniCssExtractPlugin = require("mini-css-extract-plugin");
// const { createLodashAliases } = require('lodash-loader');
const VueLoaderPlugin = require('vue-loader/lib/plugin');


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

                /*noscript: {
                    name: 'noscript',
                    chunks: 'initial',
                    enforce: true,
                    test: /noscript/,
                }*/
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
            { test: /\.vue$/, loader: 'vue-loader' },
            {
                test: /\/node_modules\//,
                sideEffects: false
            },
            {
                test: /\.scss$/,
                use: [ { loader: MiniCssExtractPlugin.loader },
                       { loader: 'css-loader' },
                       { loader: 'sass-loader' , options: { sourceMap: true }} ],
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
        ],
    },

    resolve: {
        alias: {
            js: path.resolve(__dirname, 'assets/js'),
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

