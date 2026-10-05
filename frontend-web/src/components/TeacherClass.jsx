import { createContext, useContext } from 'react'

export const TeacherClassContext = createContext('')
export const useTeacherClass = () => useContext(TeacherClassContext)
