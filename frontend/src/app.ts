/**
 * 应用入口文件
 */
import { Component } from 'react'
import './app.scss'

class App extends Component {
  componentDidMount() {
    // 应用初始化
    console.log('App mounted')
  }

  componentDidShow() {
    // 应用显示
  }

  componentDidHide() {
    // 应用隐藏
  }

  render() {
    return this.props.children
  }
}

export default App
