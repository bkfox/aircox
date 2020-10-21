const path = require('path');
const webpack = require('webpack');

const MiniCssExtractPlugin = require("mini-css-extract-plugin");
// const { createLodashAliases } = require('lodash-loader');
const { VueLoaderPlugin } = require('vue-loader');


module.exports = (env, argv) => Object({
    context: __dirname,
    entry: {
        main: './assets/public/index',
        admin: './assets/admin/index',
        streamer: './assets/streamer/index',
    },

    output: {
        path: path.resolve('aircox/static/aircox'),
        filename: '[name].js',
        chunkFilename: '[name].js',
    },

    optimization: {
        //usedExports: true,
        // concatenateModules: argv.mode == 'production' ? true : false,

        splitChunks: {
            cacheGroups: {
                vendor: {
                    name: 'vendor',
                    chunks: 'initial',
                    enforce: true,

                    test: /[\\/]node_modules[\\/]/,
                },
                /*admin: {
                    name: 'admin',
                    chunks: 'initial',
                    enforce: false,
                    test: /assets[\\/]admin[\\/]/,
                },*/

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
                test: /\.s?css$/,
                use: [ { loader: MiniCssExtractPlugin.loader },
                       { loader: 'css-loader' },
                       { loader: 'sass-loader' , options: { sourceMap: true }} ],
            },
            {
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
            vue: 'vue/dist/vue.esm.browser.js',
        },
        modules: [
            './assets',
            './node_modules',
        ],
        extensions: ['.js', '.vue', '.css', '.scss', '.styl', '.ttf']
    },
})

